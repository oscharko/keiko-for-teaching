use std::env;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Use PROTO_PATH environment variable if set, otherwise use relative path
    let proto_path = env::var("PROTO_PATH")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("../../packages/proto"));

    let proto_file = proto_path.join("ingestion/v1/ingestion.proto");

    println!("cargo:rerun-if-changed={}", proto_file.display());
    println!("cargo:rerun-if-changed={}", proto_path.display());

    tonic_build::configure()
        .build_server(true)
        .build_client(false)
        .compile_protos(
            &[proto_file.to_str().unwrap()],
            &[proto_path.to_str().unwrap()],
        )?;
    Ok(())
}

