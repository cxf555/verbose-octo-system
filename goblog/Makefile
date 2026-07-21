.PHONY: run build clean lint

# Build the server binary
build:
	go build -o goblog.exe ./cmd/server/

# Run the server
run:
	go run ./cmd/server/ -config ./configs/config.yaml

# Run with custom config
run-prod:
	go run ./cmd/server/ -config ./configs/config.yaml
	# GIN_MODE=release

# Clean build artifacts
clean:
	rm -f goblog.exe

# Run go vet
vet:
	go vet ./...

# Run golangci-lint (install first: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest)
lint:
	golangci-lint run ./...

# Download dependencies
deps:
	go mod tidy
	go mod download

# Test
test:
	go test ./... -v -count=1
