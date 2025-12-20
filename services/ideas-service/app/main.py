from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import ideas
from .services.storage import StorageService
from .services.search import SearchService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Storage Service
    if settings.azure_cosmos_connection_string:
        app.state.storage = StorageService(
            connection_string=settings.azure_cosmos_connection_string,
            database_name=settings.azure_ideas_database,
            container_name=settings.azure_ideas_container
        )
        await app.state.storage.initialize()
    else:
        # Fallback for dev/testing or raise specific warning
        # For now we'll set it to None, routes need to handle this
        app.state.storage = None
        print("WARNING: Cosmos DB connection string not set. Persistence disabled.")
        
    # Initialize Search Service
    if settings.azure_search_service and settings.azure_search_key:
        app.state.search = SearchService(
            service_name=settings.azure_search_service,
            index_name=settings.azure_search_index,
            api_key=settings.azure_search_key
        )
    else:
        app.state.search = None
        print("WARNING: Azure Search config not set. Search disabled.")
    
    yield
    
    # Cleanup if needed

app = FastAPI(
    title="Ideas Service",
    description="Service for managing innovation ideas",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ideas.router, prefix="/api")

@app.get("/health")
async def health_check():
    storage_status = "connected" if app.state.storage else "disabled"
    search_status = "connected" if app.state.search else "disabled"
    return {"status": "ok", "storage": storage_status, "search": search_status}
