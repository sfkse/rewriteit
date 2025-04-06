from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import rephrase, oauth
from src.database import engine
from src.models.database import Base
import os
from yoyo import read_migrations, get_backend

# Get database URL from environment
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/slackparaphrase")

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 