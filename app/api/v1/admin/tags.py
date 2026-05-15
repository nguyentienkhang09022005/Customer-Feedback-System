from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.admin.tagService import TagService
from app.schemas.admin.tag import TagCreate, TagUpdate, TagOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/tags", tags=["Tag Management"])


@router.get("", response_model=APIResponse[List[TagOut]], dependencies=[Depends(get_current_admin)])
def get_all_tags(db: Session = Depends(get_db)):
    tags = TagService(db).get_all_tags()
    return APIResponse(status=True, code=200, message="Success", data=tags)


@router.post("", response_model=APIResponse[TagOut], dependencies=[Depends(get_current_admin)])
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    try:
        tag = TagService(db).create_tag(data)
        return APIResponse(status=True, code=201, message="Tag created successfully", data=tag)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{tag_id}", response_model=APIResponse[TagOut], dependencies=[Depends(get_current_admin)])
def get_tag(tag_id: UUID, db: Session = Depends(get_db)):
    try:
        tag = TagService(db).get_tag_by_id(str(tag_id))
        return APIResponse(status=True, code=200, message="Success", data=tag)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.put("/{tag_id}", response_model=APIResponse[TagOut], dependencies=[Depends(get_current_admin)])
def update_tag(tag_id: UUID, data: TagUpdate, db: Session = Depends(get_db)):
    try:
        tag = TagService(db).update_tag(str(tag_id), data)
        return APIResponse(status=True, code=200, message="Tag updated successfully", data=tag)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{tag_id}", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def delete_tag(tag_id: UUID, db: Session = Depends(get_db)):
    try:
        TagService(db).delete_tag(str(tag_id))
        return APIResponse(status=True, code=200, message="Tag deleted successfully")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)