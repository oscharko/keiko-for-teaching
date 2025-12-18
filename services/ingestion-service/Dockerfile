FROM rust:1.83-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y protobuf-compiler libssl-dev pkg-config && rm -rf /var/lib/apt/lists/*

COPY Cargo.toml Cargo.lock* ./
COPY src ./src
COPY build.rs ./
COPY ../../packages/proto /proto

RUN cargo build --release

FROM debian:bookworm-slim

WORKDIR /app
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /app/target/release/keiko-ingestion /app/keiko-ingestion

USER appuser
EXPOSE 8004 50051

CMD ["/app/keiko-ingestion"]

