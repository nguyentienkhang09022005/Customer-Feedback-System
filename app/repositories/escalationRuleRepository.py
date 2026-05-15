from sqlalchemy.orm import Session
from app.models.escalationRule import EscalationRule
from typing import List, Optional


class EscalationRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, rule: EscalationRule) -> EscalationRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_all(self) -> List[EscalationRule]:
        return self.db.query(EscalationRule).all()

    def get_by_id(self, rule_id: str) -> Optional[EscalationRule]:
        return self.db.query(EscalationRule).filter(EscalationRule.id == rule_id).first()

    def get_active(self) -> List[EscalationRule]:
        return self.db.query(EscalationRule).filter(EscalationRule.is_active == True).all()

    def update(self, rule: EscalationRule) -> EscalationRule:
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule: EscalationRule) -> None:
        self.db.delete(rule)
        self.db.commit()
