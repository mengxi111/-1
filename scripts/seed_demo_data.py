import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.services.demo_seed import bootstrap_demo_data


def main() -> None:
    db = SessionLocal()
    try:
        result = bootstrap_demo_data(db, only_if_empty=False)
        print(
            "demo seed finished:",
            {
                "stores": result.stores_created,
                "areas": result.areas_created,
                "seats": result.seats_created,
                "plans": result.plans_created,
                "users": result.users_created,
                "bookings": result.bookings_created,
                "orders": result.orders_created,
                "notices": result.notices_created,
                "notifications": result.notifications_created,
            },
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
