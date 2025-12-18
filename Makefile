# Keiko for Teaching - Makefile
# Main build and development commands

.PHONY: help install build test clean validate-api generate-proto

# Default target
help:
	@echo "Keiko for Teaching - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install all dependencies"
	@echo "  make build            - Build all services and packages"
	@echo "  make test             - Run all tests"
	@echo "  make clean            - Clean build artifacts"
	@echo ""
	@echo "API & Proto:"
	@echo "  make validate-api     - Validate OpenAPI specifications"
	@echo "  make generate-proto   - Generate code from Protocol Buffers"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build all Docker images"
	@echo "  make docker-up        - Start all services with Docker Compose"
	@echo "  make docker-down      - Stop all services"
	@echo ""
	@echo "Quality:"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo ""

# Install dependencies
install:
	@echo "Installing dependencies..."
	pnpm install
	cd services/ingestion-service && cargo build
	@echo "Dependencies installed successfully!"

# Build all services
build:
	@echo "Building all services..."
	pnpm run build
	cd services/ingestion-service && cargo build --release
	@echo "Build completed successfully!"

# Run tests
test:
	@echo "Running tests..."
	pnpm run test
	cd services/ingestion-service && cargo test
	@echo "Tests completed successfully!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	pnpm run clean
	cd services/ingestion-service && cargo clean
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean completed successfully!"

# Validate OpenAPI specifications
validate-api:
	@echo "Validating OpenAPI specifications..."
	./tools/scripts/validate-openapi.sh

# Generate code from Protocol Buffers
generate-proto:
	@echo "Generating code from Protocol Buffers..."
	cd packages/proto && ./compile.sh
	@echo "Proto generation completed successfully!"

# Build Docker images
docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "Docker images built successfully!"

# Start services with Docker Compose
docker-up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started successfully!"

# Stop services
docker-down:
	@echo "Stopping services..."
	docker-compose down
	@echo "Services stopped successfully!"

# Run linters
lint:
	@echo "Running linters..."
	pnpm run lint
	cd services/ingestion-service && cargo clippy
	@echo "Linting completed successfully!"

# Format code
format:
	@echo "Formatting code..."
	pnpm run format
	cd services/ingestion-service && cargo fmt
	@echo "Formatting completed successfully!"

# Development setup
dev-setup: install generate-proto
	@echo "Development environment setup completed!"
	@echo "Run 'make docker-up' to start services"

