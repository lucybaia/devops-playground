from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app.routers import snippets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="DevStation API", version="0.1.0", lifespan=lifespan)

app.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "devstation-api"}
