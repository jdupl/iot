import datetime as dt

import math

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

# from database import db_session, Base
from server import db
from server.util import time_lt_other, tuple_to_timedelta, add_delta_to_rel_time


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)
    pins = relationship('Pin', back_populates="schedule")
    open_time_sec = Column(Integer)
    run_for_sec = Column(Integer)
    repeat_every = Column(Integer)
    repeat_until = Column(Integer)

    """Represents daily events schedule for relays."""

    def create_events(self):
        self.open_events = []
        self.close_events = []
        open_h = math.floor(self.open_time_sec / 3600)
        open_m = math.floor(self.open_time_sec % 3600 / 60)
        open_s = math.floor(self.open_time_sec % 60)
        self.first_open = dt.time(hour=open_h, minute=open_m, second=open_s)
        self.run_for = dt.timedelta(seconds=self.run_for_sec)
        t = self.first_open

        if self.repeat_every:
            # repeat_every = tuple_to_timedelta(self.repeat_every)
            repeat_every = dt.timedelta(seconds=self.repeat_every)
        else:
            self.open_events.append(t)
            self.close_events.append(add_delta_to_rel_time(t, self.run_for))
            return

        if not self.repeat_until:
            # Set max cut off if not provided
            repeat_until = dt.time(23, 59, 59)
        else:
            repeat_until = dt.time(*repeat_until)

        while True:
            last = t
            o_time = t
            c_time = add_delta_to_rel_time(t, self.run_for)

            self.open_events.append(o_time)
            self.close_events.append(c_time)

            t = add_delta_to_rel_time(t, repeat_every)

            if not time_lt_other(t, repeat_until) or time_lt_other(t, last):
                break

    def __init__(self, open_time_sec, run_for_sec, repeat_every=None,
                 repeat_until=None):
        """
        open_time: First open time of the day
        run_for_sec: Keep open for this amount of seconds
        repeat_every: Repeat each amount of time (tuple of (h, m, s)) or 'None'
                      if event shouldn't be repeated more than once a day.
                      Starts at the open time so this parameter must be
                      longer than 'run_for_sec'.
        repeat_until: Repeat schedule until (tuple of (h, m, s)) or 'None' if
                      it should be repeated until the day ends.
        """
        self.open_time_sec = open_time_sec
        self.run_for_sec = run_for_sec
        self.repeat_every = repeat_every
        self.repeat_until = repeat_until


class Pin(db.Model):
    __tablename__ = 'pins'

    id = Column(Integer, primary_key=True)
    pin_id = Column(Integer)
    user_name = Column(String)
    on_user_override = Column(Boolean)
    state_str = Column(String)

    schedule_id = Column(Integer, ForeignKey('schedules.id'))
    schedule = relationship('Schedule', back_populates='pins')

    def __init__(self, pin_id, name=None, user_override=False):
        self.pin_id = pin_id
        self.user_name = name
        self.state_str = 'off'
        self.on_user_override = user_override

    def __eq__(self, o):
        return self.pin_id == o.pin_id and \
            self.state_str == o.state_str

    def reset_user_override(self):
        # TODO trigger control relay routine
        self.on_user_override = False

    def as_pub_dict(self):
        return {
            'id': self.id,
            'pin_id': self.pin_id,
            'name': self.user_name,
            'state_str': self.state_str,
            'on_user_override': self.on_user_override
        }
