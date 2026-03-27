import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.member_card import MemberCard
from app.models.store import Store
from app.models.user import User
from app.services.bootstrap import bootstrap_initial_data


def needs_name_repair(name: str | None) -> bool:
    return not name or "?" in name


def get_or_create_users(db):
    super_admin = db.execute(select(User).where(User.phone == "13900000000")).scalar_one_or_none()
    if super_admin is None:
        super_admin = User(
            phone="13900000000",
            name="超级管理员",
            role="super_admin",
            status=1,
            password_hash=hash_password("123456"),
        )
        db.add(super_admin)
    else:
        if not super_admin.password_hash:
            super_admin.password_hash = hash_password("123456")
        if needs_name_repair(super_admin.name):
            super_admin.name = "超级管理员"

    admin = db.execute(select(User).where(User.phone == "13900000001")).scalar_one_or_none()
    if admin is None:
        admin = User(
            phone="13900000001",
            name="本地管理员",
            role="admin",
            status=1,
            password_hash=hash_password("123456"),
        )
        db.add(admin)
    else:
        if not admin.password_hash:
            admin.password_hash = hash_password("123456")
        if needs_name_repair(admin.name):
            admin.name = "本地管理员"

    staff = db.execute(select(User).where(User.phone == "13900000003")).scalar_one_or_none()
    if staff is None:
        staff = User(
            phone="13900000003",
            name="本地店员",
            role="staff",
            status=1,
            password_hash=hash_password("123456"),
        )
        db.add(staff)
    else:
        if not staff.password_hash:
            staff.password_hash = hash_password("123456")
        if needs_name_repair(staff.name):
            staff.name = "本地店员"

    student = db.execute(select(User).where(User.phone == "13900000002")).scalar_one_or_none()
    if student is None:
        student = User(
            phone="13900000002",
            name="本地学员",
            role="student",
            status=1,
            password_hash=hash_password("123456"),
        )
        db.add(student)
    else:
        if not student.password_hash:
            student.password_hash = hash_password("123456")
        if needs_name_repair(student.name):
            student.name = "本地学员"

    db.flush()
    return super_admin, admin, staff, student


def seed_member_card(db, student_id: int):
    card = db.execute(
        select(MemberCard).where(MemberCard.user_id == student_id, MemberCard.card_name == "体验时长卡")
    ).scalar_one_or_none()
    if card is None:
        db.add(
            MemberCard(
                user_id=student_id,
                card_name="体验时长卡",
                card_type="time",
                balance_minutes=600,
                balance_times=0,
                status="active",
            )
        )


def main():
    db = SessionLocal()
    try:
        bootstrap_initial_data(db, only_if_empty=False)
        with db.begin():
            _, _, _, student = get_or_create_users(db)
            seed_member_card(db, student.id)

        stores = db.scalars(select(Store).where(Store.status == 1).order_by(Store.id.asc())).all()
        print("seed local data done")
        print("active stores:", [store.name for store in stores])
    finally:
        db.close()


if __name__ == "__main__":
    main()
