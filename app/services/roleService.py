from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.roleRepository import RoleRepository
from app.models.human import Role
from app.schemas.roleSchema import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, db: Session):
        self.repo = RoleRepository(db)

    def get_all_roles(self):
        return self.repo.get_all()

    def create_role(self, data: RoleCreate):
        if self.repo.get_by_name(data.role_name):
            raise HTTPException(status_code=400, detail="Role này đã tồn tại")
        return self.repo.create(Role(**data.dict()))

    def update_role(self, role_name: str, data: RoleUpdate):
        role = self.repo.get_by_name(role_name)
        if not role: raise HTTPException(status_code=404, detail="Không tìm thấy Role")

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role, key, value)
        return self.repo.update(role)

    def delete_role(self, role_name: str):
        role = self.repo.get_by_name(role_name)
        if not role: raise HTTPException(status_code=404, detail="Không tìm thấy Role")
        self.repo.delete(role)