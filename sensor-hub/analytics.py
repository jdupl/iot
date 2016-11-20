import datetime as dt

from sqlalchemy import desc, between
from numpy.polynomial import polynomial

from models import HygroRecord


def _get_last_watering_timestamp(sensor_uuid):
    """Try to find last watering from the last 500 records of the sensor.
       A diffenrece of `watering_thresold` must be found between now and then
       to be considered a watering."""
    watering_thresold = 50  # Minimum fluctuation to consider a watering

    records = HygroRecord.query \
        .filter(HygroRecord.sensor_uuid == sensor_uuid) \
        .order_by(desc(HygroRecord.timestamp)).limit(5000).all()
    last_record = records[0]

    for current in records[1:]:

        if current.value < last_record.value \
         and last_record.value - current.value >= watering_thresold:

            return last_record.timestamp

        last_record = current


def _get_polynomial(sensor_uuid, start, stop=dt.datetime.now()):
    """
    Get a polynomial aproximation of the soil humidity function from data.
    """
    x = []
    y = []

    records = HygroRecord.query \
        .filter(HygroRecord.sensor_uuid == sensor_uuid) \
        .filter(between(HygroRecord.timestamp, start, stop)) \
        .order_by(HygroRecord.timestamp).all()

    for r in records:
        x.append((r.timestamp - start))
        y.append(int(r.value))

    if len(x) > 0:
        return polynomial.polyfit(x, y, 1)


def _predict_at(at_time, polynom, last_watering_timestamp):
    """Predict the value of the soil humidity with the provided
    polynomial and the future timestamp `at_time`.
    """
    elapsed_from_watering = (at_time - last_watering_timestamp)
    return polynomial.polyval(elapsed_from_watering, polynom)


def _predict_next_watering(polynom, last_watering_timestamp):
    """Extrapolate data with polynomial function to find next watering.
    """
    max_tries = 2016  # One week
    step = 3600  # Step in seconds
    val = 0
    time = 0
    tries = 0

    while tries <= max_tries:
        val = polynomial.polyval(time, polynom)

        if val <= 100:
            return time + last_watering_timestamp

        time += step
        tries += 1
