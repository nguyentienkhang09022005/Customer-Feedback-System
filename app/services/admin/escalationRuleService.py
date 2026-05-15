from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.escalationRuleRepository import EscalationRuleRepository
from app.models.escalationRule import EscalationRule
from app.schemas.admin.escalation import EscalationRuleCreate, EscalationRuleUpdate
from typing import List


class EscalationRuleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EscalationRuleRepository(db)

    def create_rule(self, data: EscalationRuleCreate) -> EscalationRule:
        new_rule = EscalationRule(**data.model_dump())
        return self.repo.create(new_rule)

    def get_all_rules(self) -> List[EscalationRule]:
        return self.repo.get_all()

    def get_rule(self, rule_id: str) -> EscalationRule:
        rule = self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Escalation rule not found!")
        return rule

    def get_active_rules(self) -> List[EscalationRule]:
        return self.repo.get_active()

    def update_rule(self, rule_id: str, data: EscalationRuleUpdate) -> EscalationRule:
        rule = self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Escalation rule not found!")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rule, key, value)

        return self.repo.update(rule)

    def delete_rule(self, rule_id: str) -> None:
        rule = self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Escalation rule not found!")
        self.repo.delete(rule)

    def toggle_rule(self, rule_id: str) -> EscalationRule:
        rule = self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Escalation rule not found!")
        rule.is_active = not rule.is_active
        return self.repo.update(rule)
