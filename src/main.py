from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import rephrase, oauth, subscription
import os
import logging
from logging.handlers import RotatingFileHandler
from yoyo import read_migrations, get_backend
from logtail import LogtailHandler
from src.config import settings

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.handlers = []

if os.getenv("ENV", "dev") == "prod":
    logtail_handler = LogtailHandler(
        source_token=settings.logtail_source_token,
        host=settings.logtail_host
    )
    logger.addHandler(logtail_handler)
else:
    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Get database URL from environment with correct host for Docker
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@slackparaphrase-db:5433/slackparaphrase")

# Apply migrations
backend = get_backend(database_url)
migrations = read_migrations('migrations')
backend.apply_migrations(backend.to_apply(migrations))

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rephrase.router)
app.include_router(oauth.router)
app.include_router(subscription.router)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"} 