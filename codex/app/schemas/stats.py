from datetime import date

from pydantic import BaseModel, ConfigDict


class HourlyOccupancyItem(BaseModel):
    hour: int
    occupied_seats: int
    occupancy_rate: float

    model_config = ConfigDict(from_attributes=True)


class DailyTrendItem(BaseModel):
    date: str
    booking_count: int
    revenue: float


class HotSeatItem(BaseModel):
    seat_id: int
    seat_no: str
    booking_count: int


class StatsOverviewOut(BaseModel):
    store_id: int | None
    date: date
    today_booking_count: int
    today_checkin_count: int
    today_no_show_count: int
    today_order_count: int
    today_revenue: float
    current_occupied_count: int
    current_idle_seat_count: int
    current_occupancy_rate: float
    today_occupied_count: int
    today_occupancy_rate: float
    hourly_occupancy_trend: list[HourlyOccupancyItem]
    recent_7_day_trend: list[DailyTrendItem]
    hot_seat_rank: list[HotSeatItem]


class HourlyCheckinItem(BaseModel):
    hour: int
    total_reservations: int
    checked_in_count: int
    checkin_rate: float

    model_config = ConfigDict(from_attributes=True)


class CheckinStatsOut(BaseModel):
    store_id: int | None
    date: date
    total_reservations: int
    checked_in_count: int
    missed_checkin_count: int
    checkin_rate: float
    hourly_checkin_trend: list[HourlyCheckinItem]
