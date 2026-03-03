"""FastAPI application entry point."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import files, claims, dashboard, codes, export

app = FastAPI(title="835-Cycler", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# Mount API routers
app.include_router(files.router)
app.include_router(claims.router)
app.include_router(dashboard.router)
app.include_router(codes.router)
app.include_router(export.router)

# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")


@app.get("/")
async def serve_index():
    """Serve the main SPA HTML file."""
    return FileResponse(str(frontend_dir / "index.html"))
