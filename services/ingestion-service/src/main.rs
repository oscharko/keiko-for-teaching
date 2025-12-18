mod api;
mod grpc;
mod parser;
mod splitter;

use std::net::SocketAddr;
use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "keiko_ingestion=debug,tower_http=debug".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let rest_addr: SocketAddr = "0.0.0.0:8004".parse()?;
    let grpc_addr: SocketAddr = "0.0.0.0:50051".parse()?;

    tracing::info!("Starting REST server on {}", rest_addr);
    tracing::info!("Starting gRPC server on {}", grpc_addr);

    let rest_app = api::create_router();
    let grpc_service = grpc::create_service();

    let rest_listener = TcpListener::bind(rest_addr).await?;
    let grpc_listener = TcpListener::bind(grpc_addr).await?;

    tokio::select! {
        result = axum::serve(rest_listener, rest_app) => {
            if let Err(e) = result {
                tracing::error!("REST server error: {}", e);
            }
        }
        result = tonic::transport::Server::builder()
            .add_service(grpc_service)
            .serve_with_incoming(tokio_stream::wrappers::TcpListenerStream::new(grpc_listener)) => {
            if let Err(e) = result {
                tracing::error!("gRPC server error: {}", e);
            }
        }
    }

    Ok(())
}

