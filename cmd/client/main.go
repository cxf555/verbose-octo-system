package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"text/tabwriter"

	"fingerprint/internal/model"
)

const serverURL = "http://fingerprint-server:8080"

func main() {
	fmt.Println("Banner Fingerprint Client")
	fmt.Println("Type 'help' for commands.\n")

	var data []model.Input
	var lastResult model.FingerprintResponse
	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("> ")
		if !scanner.Scan() {
			break
		}
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		cmd := strings.ToLower(parts[0])

		switch cmd {
		case "exit", "quit":
			fmt.Println("Bye.")
			return
		case "help":
			printHelp()
		case "load":
			if len(parts) < 2 {
				fmt.Println("Usage: load <file.json>")
				continue
			}
			d, err := loadFile(parts[1])
			if err != nil {
				fmt.Printf("  Error: %v\n", err)
				continue
			}
			data = d
			fmt.Printf("  Loaded %d entries.\n", len(data))
		case "send":
			if len(data) == 0 {
				fmt.Println("  No data loaded. Use 'load <file>' first.")
				continue
			}
			fmt.Printf("  Sending %d entries...\n", len(data))
			result, err := sendToServer(data)
			if err != nil {
				fmt.Printf("  Error: %v\n", err)
				continue
			}
			lastResult = result
			printResults(result)
		case "result":
			if lastResult == nil {
				fmt.Println("  No result yet. Use 'send' first.")
				continue
			}
			printResults(lastResult)
		default:
			fmt.Printf("  Unknown command: %s (type 'help')\n", cmd)
		}
	}
}

func loadFile(path string) ([]model.Input, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open: %w", err)
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		return nil, fmt.Errorf("read: %w", err)
	}

	// Try {"data": [...]} first
	var req model.FingerprintRequest
	if err := json.Unmarshal(data, &req); err == nil && req.Data != nil {
		return req.Data, nil
	}

	// Try bare array
	var arr []model.Input
	if err := json.Unmarshal(data, &arr); err != nil {
		preview := strings.TrimSpace(string(data))
		if len(preview) > 60 {
			preview = preview[:60]
		}
		return nil, fmt.Errorf("expected [{ip,port,banner}] or {data:[...]}, got: %s", preview)
	}
	return arr, nil
}

func sendToServer(data []model.Input) (model.FingerprintResponse, error) {
	body, err := json.Marshal(model.FingerprintRequest{Data: data})
	if err != nil {
		return nil, fmt.Errorf("marshal: %w", err)
	}
	url := serverURL + "/fingerprint"

	resp, err := http.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("POST: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("server returned %d: %s", resp.StatusCode, string(respBody))
	}

	var results model.FingerprintResponse
	if err := json.Unmarshal(respBody, &results); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	return results, nil
}

func printResults(results model.FingerprintResponse) {
	fmt.Println()
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "  IP\tPort\tProtocol\tProduct\tVersion\tOS\tConfidence")
	fmt.Fprintln(w, "  --\t----\t--------\t-------\t-------\t--\t----------")
	for _, r := range results {
		fmt.Fprintf(w, "  %s\t%d\t%s\t%s\t%s\t%s\t%.2f\n",
			r.IP, r.Port, r.Protocol, r.Product, r.Version, r.OSHint, r.Confidence)
	}
	w.Flush()
	fmt.Println()
}

func printHelp() {
	fmt.Println(`  Commands:
    load <file>  Load a JSON file with banner data
    send         Send loaded data to server for fingerprinting
    result       Show the last result again
    help         Show this help
    exit         Quit`)
}
