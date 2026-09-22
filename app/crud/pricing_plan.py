from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pricing_plan import PricingPlan
from app.schemas.admin_api import PlanCreate, PlanUpdate


def create_plan(db: Session, payload: PlanCreate) -> PricingPlan:
    obj = PricingPlan(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_plans(db: Session, store_id: int | None = None, skip: int = 0, limit: int = 100) -> list[PricingPlan]:
    stmt = select(PricingPlan)
    if store_id is not None:
        stmt = stmt.where(PricingPlan.store_id == store_id)
    stmt = stmt.offset(skip).limit(limit).order_by(PricingPlan.id)
    return list(db.scalars(stmt).all())


def get_plan(db: Session, plan_id: int) -> PricingPlan | None:
    return db.get(PricingPlan, plan_id)


def update_plan(db: Session, obj: PricingPlan, payload: PlanUpdate) -> PricingPlan:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_plan(db: Session, obj: PricingPlan) -> None:
    db.delete(obj)
    db.commit()

