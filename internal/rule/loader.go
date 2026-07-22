package rule

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"fingerprint/internal/model"
)

// Store holds all loaded fingerprint rules indexed by protocol.
type Store struct {
	mu    sync.RWMutex
	rules map[string]*model.RuleFile
	count int
}

// Load reads all .json rule files from dir and returns a populated Store.
func Load(dir string) (*Store, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read rules dir %s: %w", dir, err)
	}

	s := &Store{rules: make(map[string]*model.RuleFile)}
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		path := filepath.Join(dir, entry.Name())
		data, err := os.ReadFile(path)
		if err != nil {
			log.Printf("[rule] skip %s: %v", entry.Name(), err)
			continue
		}
		var rf model.RuleFile
		if err := json.Unmarshal(data, &rf); err != nil {
			log.Printf("[rule] skip %s: invalid json: %v", entry.Name(), err)
			continue
		}
		if rf.Protocol == "" {
			log.Printf("[rule] skip %s: missing protocol field", entry.Name())
			continue
		}
		s.rules[strings.ToLower(rf.Protocol)] = &rf
		log.Printf("[rule] loaded %d products for protocol %s", len(rf.Products), rf.Protocol)
	}
	s.count = len(s.rules)
	log.Printf("[rule] total %d protocols loaded", s.count)
	return s, nil
}

// Reload re-reads all rules from dir. It is safe for concurrent use.
func (s *Store) Reload(dir string) error {
	next, err := Load(dir)
	if err != nil {
		return err
	}
	s.mu.Lock()
	s.rules = next.rules
	s.count = next.count
	s.mu.Unlock()
	log.Printf("[rule] reloaded %d protocols", next.count)
	return nil
}

// Candidates returns all rule files whose default_ports include the given port,
// or all rule files if no port match is found (conservative fallback).
func (s *Store) Candidates(port int) []*model.RuleFile {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var matched []*model.RuleFile
	for _, rf := range s.rules {
		for _, p := range rf.DefaultPorts {
			if p == port {
				matched = append(matched, rf)
				break
			}
		}
	}
	if len(matched) > 0 {
		return matched
	}
	// Fallback: return all rules so we don't miss anything
	all := make([]*model.RuleFile, 0, len(s.rules))
	for _, rf := range s.rules {
		all = append(all, rf)
	}
	return all
}

// Count returns the number of loaded protocols.
func (s *Store) Count() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.count
}
