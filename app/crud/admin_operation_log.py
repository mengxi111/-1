from datetime import datetime

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.admin_operation_log import AdminOperationLog


def create_admin_operation_log(
    db: Session,
    *,
    operator_id: int | None,
    operator_name: str | None,
    operator_role: str | None,
    ip: str,
    module: str,
    request_method: str,
    request_path: str,
    status_code: int,
    content: str,
) -> AdminOperationLog:
    log = AdminOperationLog(
        operator_id=operator_id,
        operator_name=operator_name,
        operator_role=operator_role,
        ip=ip,
        module=module,
        request_method=request_method,
        request_path=request_path,
        status_code=status_code,
        content=content,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_admin_operation_logs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    module: str | None = None,
    operator_id: int | None = None,
    operator_keyword: str | None = None,
    request_method: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> tuple[int, list[AdminOperationLog]]:
    stmt = select(AdminOperationLog)
    count_stmt = select(func.count(AdminOperationLog.id))

    if module:
        stmt = stmt.where(AdminOperationLog.module == module)
        count_stmt = count_stmt.where(AdminOperationLog.module == module)
    if operator_id is not None:
        stmt = stmt.where(AdminOperationLog.operator_id == operator_id)
        count_stmt = count_stmt.where(AdminOperationLog.operator_id == operator_id)
    if operator_keyword:
        pattern = f"%{operator_keyword.strip()}%"
        condition = or_(
            AdminOperationLog.operator_name.ilike(pattern),
            cast(AdminOperationLog.operator_id, String).ilike(pattern),
        )
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if request_method:
        stmt = stmt.where(AdminOperationLog.request_method == request_method.upper())
        count_stmt = count_stmt.where(AdminOperationLog.request_method == request_method.upper())
    if start_time is not None:
        stmt = stmt.where(AdminOperationLog.created_at >= start_time)
        count_stmt = count_stmt.where(AdminOperationLog.created_at >= start_time)
    if end_time is not None:
        stmt = stmt.where(AdminOperationLog.created_at <= end_time)
        count_stmt = count_stmt.where(AdminOperationLog.created_at <= end_time)

    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.scalars(stmt.order_by(AdminOperationLog.id.desc()).offset(skip).limit(limit)).all())
    return total, items
