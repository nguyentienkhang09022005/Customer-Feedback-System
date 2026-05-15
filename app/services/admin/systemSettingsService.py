from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.systemSettingsRepository import SystemSettingsRepository
from app.models.systemSettings import SystemSettings
from app.schemas.admin.systemSettings import SystemSettingsUpdate
from typing import List


class SystemSettingsService:
    DEFAULT_SETTINGS_ID = "default"

    def __init__(self, db: Session):
        self.db = db
        self.repo = SystemSettingsRepository(db)

    def get_settings(self) -> SystemSettings:
        settings = self.repo.get(self.DEFAULT_SETTINGS_ID)
        if not settings:
            # Create default settings if not exists
            settings = SystemSettings(id=self.DEFAULT_SETTINGS_ID)
            settings = self.repo.create(settings)
        return settings

    def update_settings(self, data: SystemSettingsUpdate) -> SystemSettings:
        settings = self.get_settings()
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)
        return self.repo.update(settings)

    def get_all_settings(self) -> List[SystemSettings]:
        return self.repo.get_all_settings()
