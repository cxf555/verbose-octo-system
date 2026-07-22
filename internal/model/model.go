package model

// Input is a single banner scan entry received from the client.
type Input struct {
	IP     string `json:"ip"`
	Port   int    `json:"port"`
	Banner string `json:"banner"`
}

// Result is a single fingerprint identification result.
type Result struct {
	IP         string  `json:"ip"`
	Port       int     `json:"port"`
	Protocol   string  `json:"protocol"`
	Product    string  `json:"product"`
	Version    string  `json:"version"`
	OSHint     string  `json:"os_hint"`
	Confidence float64 `json:"confidence"`
}

// FingerprintRequest is the JSON body for POST /fingerprint.
type FingerprintRequest struct {
	Data []Input `json:"data"`
}

// FingerprintResponse is the JSON body returned by POST /fingerprint.
type FingerprintResponse []Result

// HealthResponse is the JSON body returned by GET /health.
type HealthResponse struct {
	Status      string `json:"status"`
	RulesLoaded int    `json:"rules_loaded"`
	Uptime      string `json:"uptime"`
}

// RuleFile is the top-level structure of a rule JSON file on disk.
type RuleFile struct {
	Protocol     string    `json:"protocol"`
	DefaultPorts []int     `json:"default_ports"`
	Products     []Product `json:"products"`
}

// Product describes a single software product and how to detect it.
type Product struct {
	Name       string            `json:"name"`
	Patterns   []Pattern         `json:"patterns"`
	OSPatterns map[string]string `json:"os_patterns,omitempty"`
}

// Pattern is a single regex rule for matching a banner.
type Pattern struct {
	Regex           string  `json:"regex"`
	ConfidenceBoost float64 `json:"confidence_boost"`
}
