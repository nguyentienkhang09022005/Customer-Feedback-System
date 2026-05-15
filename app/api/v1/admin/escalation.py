from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.admin.escalationRuleService import EscalationRuleService
from app.schemas.admin.escalation import EscalationRuleCreate, EscalationRuleUpdate, EscalationRuleOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/escalation-rules", tags=["Escalation Rules"])


@router.get("", response_model=APIResponse[List[EscalationRuleOut]], dependencies=[Depends(get_current_admin)])
def get_all_rules(db: Session = Depends(get_db)):
    rules = EscalationRuleService(db).get_all_rules()
    return APIResponse(status=True, code=200, message="Success", data=rules)


@router.post("", response_model=APIResponse[EscalationRuleOut], dependencies=[Depends(get_current_admin)])
def create_rule(data: EscalationRuleCreate, db: Session = Depends(get_db)):
    try:
        rule = EscalationRuleService(db).create_rule(data)
        return APIResponse(status=True, code=201, message="Escalation rule created successfully", data=rule)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{rule_id}", response_model=APIResponse[EscalationRuleOut], dependencies=[Depends(get_current_admin)])
def get_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = EscalationRuleService(db).get_rule(str(rule_id))
        return APIResponse(status=True, code=200, message="Success", data=rule)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.put("/{rule_id}", response_model=APIResponse[EscalationRuleOut], dependencies=[Depends(get_current_admin)])
def update_rule(rule_id: UUID, data: EscalationRuleUpdate, db: Session = Depends(get_db)):
    try:
        rule = EscalationRuleService(db).update_rule(str(rule_id), data)
        return APIResponse(status=True, code=200, message="Escalation rule updated successfully", data=rule)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{rule_id}", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        EscalationRuleService(db).delete_rule(str(rule_id))
        return APIResponse(status=True, code=200, message="Escalation rule deleted successfully")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{rule_id}/toggle", response_model=APIResponse[EscalationRuleOut], dependencies=[Depends(get_current_admin)])
def toggle_rule(rule_id: UUID, db: Session = Depends(get_db)):
    try:
        rule = EscalationRuleService(db).toggle_rule(str(rule_id))
        return APIResponse(status=True, code=200, message="Escalation rule toggled successfully", data=rule)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
