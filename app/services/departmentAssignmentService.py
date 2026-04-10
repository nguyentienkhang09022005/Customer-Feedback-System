from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.employeeRepository import EmployeeRepository
from app.repositories.departmentRepository import DepartmentRepository
from app.schemas.departmentAssignmentSchema import (
    DepartmentAssignmentRequest,
    DepartmentTransferRequest,
    DepartmentUnassignRequest,
    SetManagerRequest,
    EmployeeAssignmentOut,
    DepartmentMemberOut,
    DepartmentWithMembersOut,
)


class DepartmentAssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.emp_repo = EmployeeRepository(db)
        self.dept_repo = DepartmentRepository(db)

    def _build_employee_assignment_out(self, emp) -> EmployeeAssignmentOut:
        """Build EmployeeAssignmentOut từ Employee model"""
        full_name = f"{emp.first_name} {emp.last_name}".strip()
        dept_name = None
        is_manager = emp.role_name == "Manager"

        if emp.id_department:
            dept = self.dept_repo.get_by_id(emp.id_department)
            if dept:
                dept_name = dept.name

        return EmployeeAssignmentOut(
            employee_id=emp.id_employee,
            employee_code=emp.employee_code,
            full_name=full_name,
            job_title=emp.job_title,
            role_name=emp.role_name,
            department_id=emp.id_department,
            department_name=dept_name,
            is_manager=is_manager,
        )

    def _build_department_member_out(self, emp) -> DepartmentMemberOut:
        """Build DepartmentMemberOut từ Employee model"""
        full_name = f"{emp.first_name} {emp.last_name}".strip()
        return DepartmentMemberOut(
            employee_id=emp.id_employee,
            employee_code=emp.employee_code,
            full_name=full_name,
            job_title=emp.job_title,
            role_name=emp.role_name,
            is_manager=emp.role_name == "Manager",
        )

    def assign_employee_to_department(self, data: DepartmentAssignmentRequest):
        """Gán nhân viên vào phòng ban - Admin only"""
        # Kiểm tra employee tồn tại
        emp = self.emp_repo.get_by_id(str(data.employee_id))
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        # Kiểm tra department tồn tại
        dept = self.dept_repo.get_by_id(data.department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")

        # Kiểm tra department đã có manager chưa (nếu employee là Manager)
        if emp.role_name == "Manager":
            existing_manager = self.emp_repo.get_department_manager(data.department_id)
            if existing_manager and existing_manager.id_employee != emp.id_employee:
                raise HTTPException(
                    status_code=400,
                    detail=f"Phòng ban {dept.name} đã có Manager. Vui lòng chuyển Manager cũ trước."
                )

        # Gán vào phòng ban
        emp = self.emp_repo.assign_to_department(data.employee_id, data.department_id)
        return self._build_employee_assignment_out(emp)

    def transfer_employee_to_department(self, data: DepartmentTransferRequest):
        """Chuyển nhân viên sang phòng ban khác - Admin only"""
        # Kiểm tra employee tồn tại
        emp = self.emp_repo.get_by_id(str(data.employee_id))
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        # Kiểm tra department mới tồn tại
        dept = self.dept_repo.get_by_id(data.new_department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")

        # Kiểm tra nếu là Manager thì phòng ban cũ phải có Manager khác
        if emp.role_name == "Manager" and emp.id_department:
            old_manager = self.emp_repo.get_department_manager(emp.id_department)
            if old_manager and old_manager.id_employee == emp.id_employee:
                # Đây là manager duy nhất của dept cũ, cần chỉ định manager mới trước
                raise HTTPException(
                    status_code=400,
                    detail="Không thể chuyển Manager cuối cùng khỏi phòng ban. Vui lòng chỉ định Manager mới trước."
                )

        # Kiểm tra department mới đã có manager chưa (nếu employee là Manager)
        if emp.role_name == "Manager":
            new_manager = self.emp_repo.get_department_manager(data.new_department_id)
            if new_manager and new_manager.id_employee != emp.id_employee:
                raise HTTPException(
                    status_code=400,
                    detail=f"Phòng ban {dept.name} đã có Manager. Vui lòng chuyển Manager cũ trước."
                )

        # Chuyển phòng ban
        emp = self.emp_repo.assign_to_department(data.employee_id, data.new_department_id)
        return self._build_employee_assignment_out(emp)

    def remove_employee_from_department(self, data: DepartmentUnassignRequest):
        """Xóa nhân viên khỏi phòng ban - Admin only"""
        emp = self.emp_repo.get_by_id(str(data.employee_id))
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        # Kiểm tra nếu là Manager thì cần có manager khác
        if emp.role_name == "Manager" and emp.id_department:
            dept_manager = self.emp_repo.get_department_manager(emp.id_department)
            if dept_manager and dept_manager.id_employee == emp.id_employee:
                members = self.emp_repo.get_department_all_members(emp.id_department)
                other_managers = [m for m in members if m.role_name == "Manager" and m.id_employee != emp.id_employee]
                if not other_managers:
                    raise HTTPException(
                        status_code=400,
                        detail="Không thể xóa Manager cuối cùng khỏi phòng ban. Vui lòng chỉ định Manager mới trước."
                    )

        # Xóa khỏi phòng ban
        emp = self.emp_repo.remove_from_department(data.employee_id)
        return self._build_employee_assignment_out(emp)

    def set_department_manager(self, data: SetManagerRequest):
        """Chỉ định Manager cho phòng ban - Admin only"""
        # Kiểm tra employee tồn tại
        emp = self.emp_repo.get_by_id(str(data.employee_id))
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        # Kiểm tra employee có phải là Manager role không
        if emp.role_name != "Manager":
            raise HTTPException(
                status_code=400,
                detail="Chỉ nhân viên có role Manager mới có thể được chỉ định làm Manager của phòng ban"
            )

        # Kiểm tra department tồn tại
        dept = self.dept_repo.get_by_id(data.department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")

        # Kiểm tra department đã có manager chưa
        existing_manager = self.emp_repo.get_department_manager(data.department_id)
        if existing_manager and existing_manager.id_employee != emp.id_employee:
            raise HTTPException(
                status_code=400,
                detail=f"Phòng ban {dept.name} đã có Manager. Vui lòng chuyển Manager cũ trước."
            )

        # Gán vào phòng ban và set làm manager
        emp = self.emp_repo.assign_to_department(data.employee_id, data.department_id)
        return self._build_employee_assignment_out(emp)

    def get_department_with_members(self, dept_id: str):
        """Lấy thông tin phòng ban kèm danh sách thành viên - Admin/Manager"""
        dept = self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban")

        members = self.emp_repo.get_department_all_members(dept_id)
        manager = self.emp_repo.get_department_manager(dept_id)

        manager_out = self._build_department_member_out(manager) if manager else None
        members_out = [self._build_department_member_out(m) for m in members if m.id_employee != manager.id_employee] if manager else [self._build_department_member_out(m) for m in members]

        return DepartmentWithMembersOut(
            id_department=dept.id_department,
            name=dept.name,
            description=dept.description,
            is_active=dept.is_active,
            manager=manager_out,
            members=members_out,
        )

    def get_employee_assignment(self, emp_id: str):
        """Lấy thông tin phân bổ của nhân viên - Admin"""
        emp = self.emp_repo.get_by_id(emp_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        return self._build_employee_assignment_out(emp)

    def get_all_department_assignments(self):
        """Lấy tất cả phân bổ phòng ban - Admin"""
        all_emps = self.emp_repo.get_all()
        return [self._build_employee_assignment_out(emp) for emp in all_emps]
