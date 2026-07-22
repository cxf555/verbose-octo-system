package api

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"runtime"
	"time"

	"fingerprint/internal/engine"
	"fingerprint/internal/model"
	"fingerprint/internal/rule"
)

// Handler holds HTTP handler dependencies.
type Handler struct {
	engine    *engine.Engine
	store     *rule.Store
	startTime time.Time
}

// NewHandler creates a new Handler.
func NewHandler(eng *engine.Engine, store *rule.Store) *Handler {
	return &Handler{engine: eng, store: store, startTime: time.Now()}
}

// Fingerprint handles POST /fingerprint.
func (h *Handler) Fingerprint(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	var req model.FingerprintRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON: " + err.Error()})
		return
	}
	if len(req.Data) == 0 {
		writeJSON(w, http.StatusOK, model.FingerprintResponse{})
		return
	}
	if len(req.Data) > 1000 {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "max 1000 entries per request"})
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	results := h.engine.FingerprintAll(ctx, req.Data)
	writeJSON(w, http.StatusOK, results)
}

// Health handles GET /health.
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(h.startTime).Truncate(time.Second).String()
	writeJSON(w, http.StatusOK, model.HealthResponse{
		Status:      "ok",
		RulesLoaded: h.store.Count(),
		Uptime:      uptime,
	})
}

// RecoverMiddleware catches panics and returns 500.
func RecoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				buf := make([]byte, 4096)
				n := runtime.Stack(buf, false)
				log.Printf("[panic] %v\n%s", rec, buf[:n])
				writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal server error"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// LoggingMiddleware logs each request.
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("[http] %s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("[http] encode error: %v", err)
	}
}

// Router builds the HTTP mux with all routes and middleware.
func Router(h *Handler) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/fingerprint", h.Fingerprint)
	mux.HandleFunc("/health", h.Health)

	var handler http.Handler = mux
	handler = LoggingMiddleware(handler)
	handler = RecoverMiddleware(handler)
	return handler
}
