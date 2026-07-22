package main

import (
	"flag"
	"log"

	"fingerprint/internal/api"
	"fingerprint/internal/engine"
	"fingerprint/internal/rule"
)

func main() {
	addr := flag.String("addr", ":8080", "server listen address")
	rulesDir := flag.String("rules", "./rules", "path to rule JSON files directory")
	flag.Parse()

	store, err := rule.Load(*rulesDir)
	if err != nil {
		log.Fatalf("load rules: %v", err)
	}

	eng := engine.New(store)
	handler := api.NewHandler(eng, store)
	router := api.Router(handler)

	srv := api.NewServer(*addr, router)
	if err := srv.Run(); err != nil {
		log.Fatalf("server: %v", err)
	}
	log.Println("[server] exited")
}
