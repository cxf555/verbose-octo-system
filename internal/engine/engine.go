package engine

import (
	"context"
	"fmt"
	"log"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"time"

	"fingerprint/internal/model"
	"fingerprint/internal/rule"
)

// Engine performs banner fingerprint identification.
type Engine struct {
	store  *rule.Store
	worker int
}

// New creates a new Engine backed by the rule store.
func New(store *rule.Store) *Engine {
	return &Engine{store: store, worker: runtime.NumCPU()}
}

type matchResult struct {
	protocol   string
	product    string
	version    string
	osHint     string
	confidence float64
}

// FingerprintAll processes a batch of inputs concurrently and returns results
// in the same order as inputs.
func (e *Engine) FingerprintAll(ctx context.Context, inputs []model.Input) model.FingerprintResponse {
	n := len(inputs)
	results := make([]model.Result, n)
	tasks := make(chan task, n)
	var wg sync.WaitGroup

	for i := 0; i < e.worker; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for t := range tasks {
				results[t.idx] = e.fingerprintOne(ctx, t.input)
			}
		}()
	}

	for i, in := range inputs {
		tasks <- task{idx: i, input: in}
	}
	close(tasks)
	wg.Wait()

	return results
}

type task struct {
	idx   int
	input model.Input
}

func (e *Engine) fingerprintOne(ctx context.Context, in model.Input) model.Result {
	result := model.Result{
		IP:         in.IP,
		Port:       in.Port,
		Protocol:   "unknown",
		Confidence: 0,
	}

	itemCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	ch := make(chan matchResult, 1)
	go func() {
		ch <- e.match(in)
	}()

	select {
	case mr := <-ch:
		result.Protocol = mr.protocol
		result.Product = mr.product
		result.Version = mr.version
		result.OSHint = mr.osHint
		result.Confidence = mr.confidence
	case <-itemCtx.Done():
	}

	return result
}

func (e *Engine) match(in model.Input) matchResult {
	candidates := e.store.Candidates(in.Port)
	if len(candidates) == 0 {
		return matchResult{protocol: "unknown"}
	}

	type scored struct {
		protocol   string
		product    string
		version    string
		osHint     string
		confidence float64
	}
	var best scored

	for _, rf := range candidates {
		for _, prod := range rf.Products {
			for _, pat := range prod.Patterns {
				re, err := regexp.Compile(pat.Regex)
				if err != nil {
					log.Printf("[engine] bad regex for %s/%s: %v", rf.Protocol, prod.Name, err)
					continue
				}
				m := re.FindStringSubmatch(in.Banner)
				if m == nil {
					continue
				}
				version := extractVersion(re, m)
				osHint := extractOS(in.Banner, prod.OSPatterns)
				conf := computeConfidence(in.Port, rf.DefaultPorts, version != "", osHint != "", pat.ConfidenceBoost)

				if conf > best.confidence {
					best = scored{
						protocol:   rf.Protocol,
						product:    prod.Name,
						version:    version,
						osHint:     osHint,
						confidence: conf,
					}
				}
			}
		}
	}

	if best.protocol == "" {
		return matchResult{protocol: "unknown"}
	}
	return matchResult{
		protocol:   best.protocol,
		product:    best.product,
		version:    best.version,
		osHint:     best.osHint,
		confidence: best.confidence,
	}
}

func extractVersion(re *regexp.Regexp, match []string) string {
	for i, name := range re.SubexpNames() {
		if name == "version" && i < len(match) {
			return match[i]
		}
	}
	return ""
}

func extractOS(banner string, osPatterns map[string]string) string {
	for osName, pattern := range osPatterns {
		re, err := regexp.Compile(pattern)
		if err != nil {
			continue
		}
		if re.MatchString(banner) {
			return osName
		}
	}
	return ""
}

func computeConfidence(port int, defaults []int, hasVersion, hasOS bool, boost float64) float64 {
	c := 0.0
	for _, p := range defaults {
		if p == port {
			c += 0.2
			break
		}
	}
	c += 0.2
	c += boost
	if hasVersion {
		c += 0.2
	}
	if hasOS {
		c += 0.1
	}
	c = clamp(c, 0, 0.99)
	return mathRound(c, 2)
}

func clamp(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func mathRound(v float64, decimals int) float64 {
	format := fmt.Sprintf("%%.%df", decimals)
	s := fmt.Sprintf(format, v)
	var out float64
	fmt.Sscanf(strings.TrimSpace(s), "%f", &out)
	return out
}
