from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .services.storage import StorageService

from .scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Storage Service
    if settings.azure_cosmos_connection_string:
        app.state.storage = StorageService(
            connection_string=settings.azure_cosmos_connection_string,
            database_name=settings.azure_news_database,
            news_container_name=settings.azure_news_container,
            prefs_container_name=settings.azure_preferences_container
        )
        await app.state.storage.initialize()
        
        # Start Scheduler
        start_scheduler(app.state.storage)
    else:
        app.state.storage = None
        print("WARNING: Cosmos DB connection string not set. Persistence disabled.")
    
    yield
    
    shutdown_scheduler()

app = FastAPI(
    title="News Service",
    description="Service for news aggregation and personalization",
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

from .routers import news
app.include_router(news.router, prefix="/api")

@app.get("/health")
async def health_check():
    storage_status = "connected" if app.state.storage else "disabled"
    return {"status": "ok", "storage": storage_status}
