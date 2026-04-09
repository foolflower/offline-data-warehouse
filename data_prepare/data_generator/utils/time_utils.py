"""
时间分布/零点漂移/延迟注入
对应 plan.md 三、事件驱动生成法 + 特征#1零点漂移 + 特征#8迟到数据
"""
import random
from datetime import datetime, timedelta, date
import numpy as np

from config import (
    MIDNIGHT_DRIFT_RATE, PAY_DELAY_LAMBDA, PAY_DELAY_MAX_HOURS,
    SHIP_DELAY_MU, SHIP_DELAY_SIGMA, SHIP_DELAY_MIN_HOURS, SHIP_DELAY_MAX_HOURS,
    RECEIVE_DELAY_MEAN_DAYS, RECEIVE_DELAY_STD_DAYS,
    RECEIVE_DELAY_MIN_DAYS, RECEIVE_DELAY_MAX_DAYS,
    COMPLETE_DELAY_MAX_DAYS, TIME_ANOMALY_RATE,
    LATE_PAYMENT_CALLBACK_RATE,
)


# 电商真实小时权重: 双峰分布(午间10-12 + 晚间20-22为高峰, 凌晨3-6极低)
_HOUR_WEIGHTS = [
    0.008, 0.005, 0.003, 0.002, 0.002, 0.003,  # 0-5点
    0.008, 0.015, 0.025, 0.050, 0.075, 0.080,  # 6-11点
    0.065, 0.055, 0.060, 0.055, 0.050, 0.045,  # 12-17点
    0.050, 0.065, 0.085, 0.090, 0.070, 0.034,  # 18-23点
]


def random_time_on_day(day: date, rng: np.random.Generator = None) -> datetime:
    """在给定日期内按电商双峰时段分布生成随机时刻"""
    h = random.choices(range(24), weights=_HOUR_WEIGHTS, k=1)[0]
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(day.year, day.month, day.day, h, m, s)


def midnight_drift_time(day: date) -> datetime:
    """
    特征#1 零点漂移: 生成23:50-23:59的时间
    5%订单create_time在此区间, payment在次日00:00-00:10
    """
    h = 23
    m = random.randint(50, 59)
    s = random.randint(0, 59)
    return datetime(day.year, day.month, day.day, h, m, s)


def midnight_drift_next_day(day: date) -> datetime:
    """零点漂移的支付时间: 次日00:00-00:10"""
    next_day = day + timedelta(days=1)
    m = random.randint(0, 10)
    s = random.randint(0, 59)
    return datetime(next_day.year, next_day.month, next_day.day, 0, m, s)


def should_midnight_drift() -> bool:
    return random.random() < MIDNIGHT_DRIFT_RATE


def pay_delay_minutes() -> float:
    """
    下单→支付: 指数分布, 中位数30分钟 (1-72h范围)
    """
    delay = random.expovariate(PAY_DELAY_LAMBDA)
    delay = max(1.0, min(delay, PAY_DELAY_MAX_HOURS * 60))
    return delay


def ship_delay_hours() -> float:
    """
    支付→发货: 对数正态, 中位数12小时 (2h-3天)
    """
    delay = random.lognormvariate(SHIP_DELAY_MU, SHIP_DELAY_SIGMA)
    delay = max(SHIP_DELAY_MIN_HOURS, min(delay, SHIP_DELAY_MAX_HOURS))
    return delay


def receive_delay_days() -> float:
    """
    发货→收货: 正态, 均值3天 (1-7天)
    """
    delay = random.gauss(RECEIVE_DELAY_MEAN_DAYS, RECEIVE_DELAY_STD_DAYS)
    delay = max(RECEIVE_DELAY_MIN_DAYS, min(delay, RECEIVE_DELAY_MAX_DAYS))
    return delay


def complete_delay_days() -> float:
    """收货→完成: 0~15天"""
    return random.uniform(0, COMPLETE_DELAY_MAX_DAYS)


def add_minutes(dt: datetime, minutes: float) -> datetime:
    return dt + timedelta(minutes=minutes)


def add_hours(dt: datetime, hours: float) -> datetime:
    return dt + timedelta(hours=hours)


def add_days(dt: datetime, days: float) -> datetime:
    return dt + timedelta(days=days)


def should_time_anomaly() -> bool:
    """特征#10: 0.5%时间逻辑问题"""
    return random.random() < TIME_ANOMALY_RATE


def late_callback_delay_hours() -> float:
    """特征#8: 支付callback延迟1-24h"""
    return random.uniform(1, 24)


def should_late_callback() -> bool:
    return random.random() < LATE_PAYMENT_CALLBACK_RATE


def fmt_datetime(dt: datetime) -> str:
    """格式化为MySQL DATETIME (f-string优化, 避免strftime开销)"""
    if dt is None:
        return ''
    return f"{dt.year}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def fmt_date(d) -> str:
    """格式化为日期字符串 (f-string优化)"""
    if d is None:
        return ''
    return f"{d.year}-{d.month:02d}-{d.day:02d}"
