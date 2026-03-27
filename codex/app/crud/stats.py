from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.stats import CheckinStatsOut, DailyTrendItem, HotSeatItem, HourlyCheckinItem, HourlyOccupancyItem, StatsOverviewOut

ORDERS_OVERVIEW_SQL = """
SELECT
    COALESCE(COUNT(*) FILTER (WHERE o.status IN ('paid','refunded')), 0) AS today_order_count,
    COALESCE(SUM(CASE WHEN o.status = 'paid' THEN o.amount ELSE 0 END), 0) AS today_revenue
FROM orders o
JOIN bookings b ON b.id = o.booking_id
JOIN seats s ON s.id = b.seat_id
WHERE o.created_at >= :day_start
  AND o.created_at < :day_end
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

BOOKINGS_OVERVIEW_SQL = """
SELECT COALESCE(COUNT(*)::int, 0) AS today_booking_count
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.start_time >= :day_start
  AND b.start_time < :day_end
  AND b.status IN ('booked', 'checked_in', 'completed', 'expired')
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

TODAY_CHECKIN_SQL = """
SELECT COALESCE(COUNT(*)::int, 0) AS today_checkin_count
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.checked_in_at >= :day_start
  AND b.checked_in_at < :day_end
  AND b.status IN ('checked_in', 'completed')
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

TODAY_NO_SHOW_SQL = """
SELECT COALESCE(COUNT(*)::int, 0) AS today_no_show_count
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.start_time >= :day_start
  AND b.start_time < :day_end
  AND b.status = 'expired'
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

AVAILABLE_SEATS_SQL = """
SELECT COALESCE(COUNT(*)::int, 0) AS total_available_seats
FROM seats s
WHERE s.is_available = TRUE
  AND s.seat_status = 'available'
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

CURRENT_OCCUPIED_SQL = """
SELECT COALESCE(COUNT(DISTINCT b.seat_id)::int, 0) AS occupied_seats
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.status IN ('booked', 'checked_in')
  AND b.start_time <= :now_at
  AND b.end_time > :now_at
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

TODAY_OCCUPIED_SQL = """
SELECT COALESCE(COUNT(DISTINCT b.seat_id)::int, 0) AS occupied_seats
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.status IN ('booked', 'checked_in', 'completed')
  AND b.start_time < :day_end
  AND b.end_time > :day_start
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

HOURLY_OCCUPANCY_SQL = """
WITH hours AS (
    SELECT generate_series(
        CAST(:day_start AS timestamptz),
        CAST(:day_end AS timestamptz) - interval '1 hour',
        interval '1 hour'
    ) AS hour_start
)
SELECT
    EXTRACT(HOUR FROM h.hour_start)::int AS hour,
    (
        SELECT COALESCE(COUNT(DISTINCT b.seat_id), 0)
        FROM bookings b
        JOIN seats s ON s.id = b.seat_id
        WHERE b.status IN ('booked', 'checked_in', 'completed')
          AND b.start_time < h.hour_start + interval '1 hour'
          AND b.end_time > h.hour_start
          AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
    )::int AS occupied_seats
FROM hours h
ORDER BY hour
"""

SEVEN_DAY_TREND_SQL = """
WITH days AS (
    SELECT generate_series(
        CAST(:day_start AS date) - interval '6 day',
        CAST(:day_start AS date),
        interval '1 day'
    )::date AS day
)
SELECT
    d.day::text AS day,
    COALESCE(
        (
            SELECT COUNT(*)
            FROM bookings b
            JOIN seats s ON s.id = b.seat_id
            WHERE b.start_time >= d.day::timestamptz
              AND b.start_time < (d.day::timestamptz + interval '1 day')
              AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
        ),
        0
    )::int AS booking_count,
    COALESCE(
        (
            SELECT SUM(o.amount)
            FROM orders o
            JOIN bookings b ON b.id = o.booking_id
            JOIN seats s ON s.id = b.seat_id
            WHERE o.created_at >= d.day::timestamptz
              AND o.created_at < (d.day::timestamptz + interval '1 day')
              AND o.status = 'paid'
              AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
        ),
        0
    )::numeric AS revenue
FROM days d
ORDER BY d.day
"""

HOT_SEAT_SQL = """
SELECT
    b.seat_id,
    s.seat_no,
    COUNT(*)::int AS booking_count
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.start_time >= :day_start
  AND b.start_time < :day_end
  AND b.status IN ('booked','checked_in','completed','expired')
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
GROUP BY b.seat_id, s.seat_no
ORDER BY booking_count DESC, b.seat_id ASC
LIMIT 5
"""

CHECKIN_OVERVIEW_SQL = """
SELECT
    COALESCE(COUNT(*)::int, 0) AS total_reservations,
    COALESCE(
        COUNT(*) FILTER (
            WHERE b.status IN ('checked_in','completed')
              AND b.checked_in_at IS NOT NULL
        )::int,
        0
    ) AS checked_in_count,
    COALESCE(COUNT(*) FILTER (WHERE b.status = 'expired')::int, 0) AS missed_checkin_count
FROM bookings b
JOIN seats s ON s.id = b.seat_id
WHERE b.start_time >= :day_start
  AND b.start_time < :day_end
  AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
"""

HOURLY_CHECKIN_SQL = """
WITH hours AS (
    SELECT generate_series(
        CAST(:day_start AS timestamptz),
        CAST(:day_end AS timestamptz) - interval '1 hour',
        interval '1 hour'
    ) AS hour_start
)
SELECT
    EXTRACT(HOUR FROM h.hour_start)::int AS hour,
    (
        SELECT COALESCE(COUNT(*)::int, 0)
        FROM bookings b
        JOIN seats s ON s.id = b.seat_id
        WHERE b.start_time >= h.hour_start
          AND b.start_time < h.hour_start + interval '1 hour'
          AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
    ) AS total_reservations,
    (
        SELECT COALESCE(COUNT(*)::int, 0)
        FROM bookings b
        JOIN seats s ON s.id = b.seat_id
        WHERE b.start_time >= h.hour_start
          AND b.start_time < h.hour_start + interval '1 hour'
          AND b.status IN ('checked_in', 'completed')
          AND b.checked_in_at IS NOT NULL
          AND (CAST(:store_id AS BIGINT) IS NULL OR s.store_id = CAST(:store_id AS BIGINT))
    ) AS checked_in_count
FROM hours h
ORDER BY hour
"""


def _date_window(target_date: date) -> tuple[datetime, datetime]:
    day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    return day_start, day_end


def _scalar_int(db: Session, sql: str, params: dict, key: str) -> int:
    row = db.execute(text(sql), params).mappings().first()
    if not row:
        return 0
    return int(row.get(key) or 0)


def _scalar_float(db: Session, sql: str, params: dict, key: str) -> float:
    row = db.execute(text(sql), params).mappings().first()
    if not row:
        return 0.0
    return float(row.get(key) or 0)


def get_overview_stats(db: Session, target_date: date, store_id: int | None) -> tuple[StatsOverviewOut, dict[str, str]]:
    day_start, day_end = _date_window(target_date)
    now_at = datetime.now(timezone.utc)
    params = {
        "store_id": store_id,
        "day_start": day_start,
        "day_end": day_end,
        "now_at": now_at,
    }

    total_available_seats = _scalar_int(db, AVAILABLE_SEATS_SQL, params, "total_available_seats")
    today_booking_count = _scalar_int(db, BOOKINGS_OVERVIEW_SQL, params, "today_booking_count")
    today_checkin_count = _scalar_int(db, TODAY_CHECKIN_SQL, params, "today_checkin_count")
    today_no_show_count = _scalar_int(db, TODAY_NO_SHOW_SQL, params, "today_no_show_count")
    occupied_today = _scalar_int(db, TODAY_OCCUPIED_SQL, params, "occupied_seats")
    current_occupied_count = _scalar_int(db, CURRENT_OCCUPIED_SQL, params, "occupied_seats")

    order_row = db.execute(text(ORDERS_OVERVIEW_SQL), params).mappings().first() or {}
    today_order_count = int(order_row.get("today_order_count") or 0)
    today_revenue = float(order_row.get("today_revenue") or 0)

    today_occupancy_rate = round((occupied_today / total_available_seats) * 100, 2) if total_available_seats > 0 else 0.0
    current_idle_seat_count = max(total_available_seats - current_occupied_count, 0)
    current_occupancy_rate = round((current_occupied_count / total_available_seats) * 100, 2) if total_available_seats > 0 else 0.0

    hourly_rows = db.execute(text(HOURLY_OCCUPANCY_SQL), params).mappings().all()
    occupancy_trend = [
        HourlyOccupancyItem(
            hour=int(row["hour"]),
            occupied_seats=int(row["occupied_seats"] or 0),
            occupancy_rate=round(((int(row["occupied_seats"] or 0) / total_available_seats) * 100), 2) if total_available_seats > 0 else 0.0,
        )
        for row in hourly_rows
    ]

    seven_day_rows = db.execute(text(SEVEN_DAY_TREND_SQL), params).mappings().all()
    recent_7_day_trend = [
        DailyTrendItem(
            date=str(row["day"]),
            booking_count=int(row["booking_count"] or 0),
            revenue=float(row["revenue"] or 0),
        )
        for row in seven_day_rows
    ]

    hot_rows = db.execute(text(HOT_SEAT_SQL), params).mappings().all()
    hot_seat_rank = [
        HotSeatItem(
            seat_id=int(row["seat_id"]),
            seat_no=str(row["seat_no"]),
            booking_count=int(row["booking_count"] or 0),
        )
        for row in hot_rows
    ]

    stats = StatsOverviewOut(
        store_id=store_id,
        date=target_date,
        today_booking_count=today_booking_count,
        today_checkin_count=today_checkin_count,
        today_no_show_count=today_no_show_count,
        today_order_count=today_order_count,
        today_revenue=today_revenue,
        current_occupied_count=current_occupied_count,
        current_idle_seat_count=current_idle_seat_count,
        current_occupancy_rate=current_occupancy_rate,
        today_occupied_count=occupied_today,
        today_occupancy_rate=today_occupancy_rate,
        hourly_occupancy_trend=occupancy_trend,
        recent_7_day_trend=recent_7_day_trend,
        hot_seat_rank=hot_seat_rank,
    )

    used_sql = {
        "bookings_overview": BOOKINGS_OVERVIEW_SQL.strip(),
        "today_checkins": TODAY_CHECKIN_SQL.strip(),
        "today_no_shows": TODAY_NO_SHOW_SQL.strip(),
        "orders_overview": ORDERS_OVERVIEW_SQL.strip(),
        "available_seats": AVAILABLE_SEATS_SQL.strip(),
        "current_occupied": CURRENT_OCCUPIED_SQL.strip(),
        "today_occupied": TODAY_OCCUPIED_SQL.strip(),
        "hourly_occupancy": HOURLY_OCCUPANCY_SQL.strip(),
        "seven_day_trend": SEVEN_DAY_TREND_SQL.strip(),
        "hot_seat_rank": HOT_SEAT_SQL.strip(),
    }
    return stats, used_sql


def get_checkin_stats(db: Session, target_date: date, store_id: int | None) -> tuple[CheckinStatsOut, dict[str, str]]:
    day_start, day_end = _date_window(target_date)
    params = {
        "store_id": store_id,
        "day_start": day_start,
        "day_end": day_end,
    }

    overview_row = db.execute(text(CHECKIN_OVERVIEW_SQL), params).mappings().first() or {}
    total_reservations = int(overview_row.get("total_reservations") or 0)
    checked_in_count = int(overview_row.get("checked_in_count") or 0)
    missed_checkin_count = int(overview_row.get("missed_checkin_count") or 0)
    checkin_rate = round((checked_in_count / total_reservations) * 100, 2) if total_reservations > 0 else 0.0

    hourly_rows = db.execute(text(HOURLY_CHECKIN_SQL), params).mappings().all()
    hourly_items: list[HourlyCheckinItem] = []
    for row in hourly_rows:
        hourly_total = int(row["total_reservations"] or 0)
        hourly_checked = int(row["checked_in_count"] or 0)
        hourly_rate = round((hourly_checked / hourly_total) * 100, 2) if hourly_total > 0 else 0.0
        hourly_items.append(
            HourlyCheckinItem(
                hour=int(row["hour"]),
                total_reservations=hourly_total,
                checked_in_count=hourly_checked,
                checkin_rate=hourly_rate,
            )
        )

    stats = CheckinStatsOut(
        store_id=store_id,
        date=target_date,
        total_reservations=total_reservations,
        checked_in_count=checked_in_count,
        missed_checkin_count=missed_checkin_count,
        checkin_rate=checkin_rate,
        hourly_checkin_trend=hourly_items,
    )
    used_sql = {
        "checkin_overview": CHECKIN_OVERVIEW_SQL.strip(),
        "hourly_checkin": HOURLY_CHECKIN_SQL.strip(),
    }
    return stats, used_sql
