"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_NAME, APP_VERSION, APP_AUTHOR, settings as app_settings
from app.database import init_db
from app.routers import files, claims, dashboard, codes, export, analytics, flags, settings, compare, api_keys, search

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()

# App info endpoint
@app.get("/api/info")
async def app_info():
    return {"name": APP_NAME, "version": APP_VERSION, "author": APP_AUTHOR}

# Mount API routers
app.include_router(files.router)
app.include_router(claims.router)
app.include_router(dashboard.router)
app.include_router(codes.router)
app.include_router(export.router)
app.include_router(analytics.router)
app.include_router(flags.router)
app.include_router(settings.router)
app.include_router(compare.router)
app.include_router(api_keys.router)
app.include_router(search.router)

# Serve frontend static files — adjust path for PyInstaller bundle
frontend_dir = app_settings.BASE_DIR / "frontend"
app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")


@app.get("/")
async def serve_index():
    """Serve the main SPA HTML file."""
    return FileResponse(str(frontend_dir / "index.html"))
