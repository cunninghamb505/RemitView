"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_NAME, APP_VERSION, APP_AUTHOR, settings as app_settings
from app.database import init_db
from app.routers import files, claims, dashboard, codes, export, analytics, flags, settings, compare, api_keys, search, ingest, listeners, developer

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    # In demo mode, auto-load sample data if DB is empty
    if app_settings.DEMO_MODE:
        from app.services import file_service
        existing = file_service.list_files()
        if not existing:
            from app.parser.sample_835 import SAMPLES
            for filename, content in SAMPLES:
                file_service.parse_and_store(content, filename)

# App info endpoint
@app.get("/api/info")
async def app_info():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR,
        "demo": app_settings.DEMO_MODE,
    }

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
app.include_router(ingest.router)
app.include_router(listeners.router)
app.include_router(developer.router)

# Serve frontend static files — adjust path for PyInstaller bundle
frontend_dir = app_settings.BASE_DIR / "frontend"
app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")


@app.get("/")
async def serve_index():
    """Serve the main SPA HTML file."""
    return FileResponse(str(frontend_dir / "index.html"))
