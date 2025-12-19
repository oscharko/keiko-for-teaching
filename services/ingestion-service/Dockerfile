# Build from repository root: docker build -t ingestion-service -f services/ingestion-service/Dockerfile .
FROM rust:1.83-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y protobuf-compiler libssl-dev pkg-config && rm -rf /var/lib/apt/lists/*

# Copy proto files first to the expected location
COPY packages/proto /app/packages/proto

# Copy Cargo files
COPY services/ingestion-service/Cargo.toml services/ingestion-service/Cargo.lock* ./
COPY services/ingestion-service/src ./src
COPY services/ingestion-service/build.rs ./

# Set environment variable for proto path (used by build.rs)
ENV PROTO_PATH=/app/packages/proto

RUN cargo build --release

FROM debian:bookworm-slim

WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/target/release/keiko-ingestion /app/keiko-ingestion

USER appuser
EXPOSE 8004 50051

CMD ["/app/keiko-ingestion"]

