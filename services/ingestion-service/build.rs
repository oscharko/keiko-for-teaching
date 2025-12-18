fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(false)
        .compile_protos(
            &["../../packages/proto/ingestion/v1/ingestion.proto"],
            &["../../packages/proto"],
        )?;
    Ok(())
}

