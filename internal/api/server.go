package api

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// Server wraps an http.Server with graceful shutdown logic.
type Server struct {
	http *http.Server
}

// NewServer creates a Server bound to addr with the given handler.
func NewServer(addr string, handler http.Handler) *Server {
	return &Server{
		http: &http.Server{
			Addr:         addr,
			Handler:      handler,
			ReadTimeout:  10 * time.Second,
			WriteTimeout: 35 * time.Second, // longer than the 30s fingerprint timeout
			IdleTimeout:  60 * time.Second,
		},
	}
}

// Run starts the server and blocks until SIGINT/SIGTERM, then shuts down gracefully.
func (s *Server) Run() error {
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Printf("[server] listening on %s", s.http.Addr)
		if err := s.http.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[server] ListenAndServe: %v", err)
		}
	}()

	sig := <-quit
	log.Printf("[server] received %v, shutting down gracefully", sig)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return s.http.Shutdown(ctx)
}
