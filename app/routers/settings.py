"""Settings endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services import settings_service


router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("")
async def get_settings():
    """Get all application settings."""
    return settings_service.get_all_settings()


@router.put("")
async def update_setting(data: SettingUpdate):
    """Update a setting."""
    result = settings_service.set_setting(data.key, data.value)
    return result
