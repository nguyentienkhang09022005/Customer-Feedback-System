from sqlalchemy.orm import Session
from app.models.systemSettings import SystemSettings
from typing import Optional, List


class SystemSettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_settings(self) -> List[SystemSettings]:
        return self.db.query(SystemSettings).all()

    def get(self, settings_id: str) -> Optional[SystemSettings]:
        return self.db.query(SystemSettings).filter(SystemSettings.id == settings_id).first()

    def create(self, settings: SystemSettings) -> SystemSettings:
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def update(self, settings: SystemSettings) -> SystemSettings:
        self.db.commit()
        self.db.refresh(settings)
        return settings
