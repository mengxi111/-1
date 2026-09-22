from dataclasses import dataclass
from datetime import time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.area import Area
from app.models.booking import Booking
from app.models.pricing_plan import PricingPlan
from app.models.seat import Seat
from app.models.store import Store


DEMO_STORES = (
    {
        "name": "图书馆自习室",
        "address": "图书馆",
        "contact_phone": "13888888888",
        "description": "位于图书馆馆内，适合安静阅读、备考复习和日常自习。",
        "seat_total": 200,
    },
    {
        "name": "杏花书院自习室",
        "address": "杏花书院创意工坊",
        "contact_phone": "13888888888",
        "description": "位于杏花书院创意工坊，适合书院活动后延续学习与讨论。",
        "seat_total": 40,
    },
    {
        "name": "青藤书院自习室",
        "address": "青藤书院1楼大厅",
        "contact_phone": "13888888888",
        "description": "位于青藤书院1楼大厅，进出便利，适合白天集中学习。",
        "seat_total": 40,
    },
    {
        "name": "三达书院自习室",
        "address": "三达书院二楼",
        "contact_phone": "13888888888",
        "description": "位于三达书院二楼，环境稳定安静，适合备考和长期自习。",
        "seat_total": 40,
    },
    {
        "name": "二餐三楼自习室",
        "address": "2号餐厅3楼",
        "contact_phone": "13888888888",
        "description": "",
        "seat_total": 200,
    },
)

LEGACY_STORE_NAMES = (
    "杭州·滨江自习室",
    "本地演示门店",
    "主校区自习室",
    "二餐二楼自习室",
)

AREA_CONFIG = (
    ("A区", "A"),
    ("B区", "B"),
)
PLAN_NAME = "按小时 5 元"
PLAN_PRICE = Decimal("5.00")


@dataclass
class BootstrapResult:
    stores_created: int = 0
    areas_created: int = 0
    seats_created: int = 0
    plans_created: int = 0

    @property
    def total_created(self) -> int:
        return self.stores_created + self.areas_created + self.seats_created + self.plans_created


def _count(db: Session, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def _core_data_is_empty(db: Session) -> bool:
    return (
        _count(db, Store) == 0
        and _count(db, Area) == 0
        and _count(db, Seat) == 0
        and _count(db, PricingPlan) == 0
    )


def _get_or_create_store(db: Session, result: BootstrapResult, config: dict[str, str]) -> Store:
    store = db.scalar(select(Store).where(Store.name == config["name"]))
    if store is not None:
        changed = False
        if store.address != config["address"]:
            store.address = config["address"]
            changed = True
        if store.contact_phone != config["contact_phone"]:
            store.contact_phone = config["contact_phone"]
            changed = True
        if store.description != config["description"]:
            store.description = config["description"]
            changed = True
        if store.status != 1:
            store.status = 1
            changed = True
        if store.open_time != time(hour=8, minute=0):
            store.open_time = time(hour=8, minute=0)
            changed = True
        if store.close_time != time(hour=23, minute=0):
            store.close_time = time(hour=23, minute=0)
            changed = True
        if changed:
            db.add(store)
        return store

    store = Store(
        name=config["name"],
        address=config["address"],
        contact_phone=config["contact_phone"],
        description=config["description"],
        status=1,
        open_time=time(hour=8, minute=0),
        close_time=time(hour=23, minute=0),
    )
    db.add(store)
    db.flush()
    result.stores_created += 1
    return store


def _normalize_legacy_demo_stores(db: Session) -> None:
    existing_store_names = {
        name
        for name in db.scalars(select(Store.name).order_by(Store.id.asc())).all()
    }
    missing_configs = [config for config in DEMO_STORES if config["name"] not in existing_store_names]
    if not missing_configs:
        return

    legacy_stores = list(
        db.scalars(
            select(Store)
            .where(Store.name.in_(LEGACY_STORE_NAMES))
            .order_by(Store.id.asc())
        ).all()
    )

    for legacy_store, target_config in zip(legacy_stores, missing_configs):
        legacy_store.name = target_config["name"]
        legacy_store.address = target_config["address"]
        legacy_store.contact_phone = target_config["contact_phone"]
        legacy_store.description = target_config["description"]
        legacy_store.status = 1
        legacy_store.open_time = time(hour=8, minute=0)
        legacy_store.close_time = time(hour=23, minute=0)
        db.add(legacy_store)


def _cleanup_duplicate_demo_stores(db: Session) -> None:
    for config in DEMO_STORES:
        stores = list(
            db.scalars(
                select(Store)
                .where(Store.name == config["name"])
                .order_by(Store.id.asc())
            ).all()
        )
        if len(stores) <= 1:
            continue

        for duplicate in stores[1:]:
            booking_count = int(
                db.scalar(select(func.count()).select_from(Booking).where(Booking.store_id == duplicate.id)) or 0
            )
            if booking_count > 0:
                continue
            db.delete(duplicate)


def _get_or_create_area(
    db: Session,
    result: BootstrapResult,
    store_id: int,
    area_name: str,
    area_code: str,
) -> Area:
    area = db.scalar(
        select(Area).where(
            Area.store_id == store_id,
            Area.code == area_code,
        )
    )
    if area is not None:
        return area

    sort_order = 1 if area_code == "A" else 2
    area = Area(store_id=store_id, name=area_name, code=area_code, sort_order=sort_order)
    db.add(area)
    db.flush()
    result.areas_created += 1
    return area


def _get_target_seats_per_area(config: dict[str, str | int]) -> int:
    total = int(config.get("seat_total", 40))
    area_count = len(AREA_CONFIG)
    if area_count <= 0:
        return total
    return max(1, total // area_count)


def _sync_area_seats(
    db: Session,
    result: BootstrapResult,
    store_id: int,
    area_id: int,
    prefix: str,
    target_count: int,
) -> None:
    existing_seats = list(
        db.scalars(
            select(Seat)
            .where(
                Seat.store_id == store_id,
                Seat.seat_no.like(f"{prefix}%"),
            )
            .order_by(Seat.id.asc())
        ).all()
    )
    existing_by_no = {seat.seat_no: seat for seat in existing_seats}

    for i in range(1, target_count + 1):
        seat_no = f"{prefix}{i:02d}"
        existing = existing_by_no.get(seat_no)
        if existing is not None:
            changed = False
            if existing.area_id != area_id:
                existing.area_id = area_id
                changed = True
            if existing.seat_type != "normal":
                existing.seat_type = "normal"
                changed = True
            if existing.seat_status != "available":
                existing.seat_status = "available"
                changed = True
            if not existing.is_available:
                existing.is_available = True
                changed = True
            if changed:
                db.add(existing)
            continue

        db.add(
            Seat(
                store_id=store_id,
                area_id=area_id,
                seat_no=seat_no,
                seat_type="normal",
                seat_status="available",
                is_available=True,
            )
        )
        result.seats_created += 1

    for seat in existing_seats:
        if not seat.seat_no.startswith(prefix):
            continue
        suffix = seat.seat_no[len(prefix) :]
        if not suffix.isdigit():
            continue
        if int(suffix) <= target_count:
            continue
        booking_count = int(
            db.scalar(select(func.count()).select_from(Booking).where(Booking.seat_id == seat.id)) or 0
        )
        if booking_count > 0:
            continue
        db.delete(seat)


def _get_or_create_plan(db: Session, result: BootstrapResult, store_id: int) -> None:
    plan = db.scalar(
        select(PricingPlan).where(
            PricingPlan.store_id == store_id,
            PricingPlan.name == PLAN_NAME,
            PricingPlan.billing_type == "hour",
        )
    )
    if plan is not None:
        return

    db.add(
        PricingPlan(
            store_id=store_id,
            name=PLAN_NAME,
            billing_type="hour",
            price=PLAN_PRICE,
            status="active",
        )
    )
    result.plans_created += 1


def bootstrap_initial_data(db: Session, only_if_empty: bool) -> BootstrapResult:
    result = BootstrapResult()

    if only_if_empty and not _core_data_is_empty(db):
        return result

    try:
        _normalize_legacy_demo_stores(db)

        for store_config in DEMO_STORES:
            store = _get_or_create_store(db=db, result=result, config=store_config)
            area_by_code: dict[str, Area] = {}
            target_seats_per_area = _get_target_seats_per_area(store_config)

            for area_name, area_code in AREA_CONFIG:
                area_by_code[area_code] = _get_or_create_area(
                    db=db,
                    result=result,
                    store_id=store.id,
                    area_name=area_name,
                    area_code=area_code,
                )

            for _, area_code in AREA_CONFIG:
                area = area_by_code[area_code]
                _sync_area_seats(
                    db=db,
                    result=result,
                    store_id=store.id,
                    area_id=area.id,
                    prefix=area_code,
                    target_count=target_seats_per_area,
                )

            _get_or_create_plan(db=db, result=result, store_id=store.id)

        _cleanup_duplicate_demo_stores(db)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
