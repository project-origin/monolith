from typing import List
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from marshmallow import validates_schema, ValidationError


class Unit(Enum):
    Wh = 1
    KWh = 10**3
    MWh = 10**6
    GWh = 10**9


@dataclass
class DataSet:
    label: str
    values: List[int] = field(default_factory=list)
    unit: Unit = Unit.Wh


@dataclass
class DateRange:
    begin: date
    end: date

    @validates_schema
    def validate_begin_before_end(self, data, **kwargs):
        if data['begin'] > data['end']:
            raise ValidationError({
                'begin': ['Must be before end'],
                'end': ['Must be after begin'],
            })

    @property
    def delta(self):
        """
        :rtype: timedelta
        """
        return self.end - self.begin

    def with_boundaries(self, begin, end):
        """
        :param date begin:
        :param date end:
        :rtype: DateRange
        """
        return DateRange(
            begin=max(begin, min(end, self.begin)),
            end=max(begin, min(end, self.end)),
        )

    def to_datetime_range(self):
        """
        :rtype: DateTimeRange
        """
        return DateTimeRange.from_date_range(self)


@dataclass
class DateTimeRange:
    begin: datetime
    end: datetime

    @validates_schema
    def validate_input(self, data, **kwargs):
        if data['begin'].utcoffset() != data['end'].utcoffset():
            raise ValidationError({
                'begin': ['Must have same time offset as end'],
                'end': ['Must have same time offset as begin'],
            })

        if data['begin'] > data['end']:
            raise ValidationError({
                'begin': ['Must be before end'],
                'end': ['Must be after begin'],
            })

    @classmethod
    def from_date_range(cls, date_range):
        """
        :param DateRange date_range:
        :rtype: DateTimeRange
        """
        return DateTimeRange(
            begin=datetime.fromordinal(date_range.begin.toordinal()),
            end=datetime.fromordinal(date_range.end.toordinal()) + timedelta(days=1),
        )

    @property
    def delta(self):
        """
        :rtype: timedelta
        """
        return self.end - self.begin


class SummaryResolution(IntEnum):
    all = 0
    year = 1
    month = 2
    day = 3
    hour = 4


@dataclass
class SummaryGroup:
    group: List[str] = field(default_factory=list)
    values: List[int] = field(default_factory=list)


class LabelRange(object):
    """
    Generates an ordered list of labels each corresponding to a period
    of time (defined by its begin, end, and the "resolution" parameter).

    For example, provided the following inputs::

        begin = datetime(2020, 1, 1, 0, 0, 0)
        end = datetime(2020, 1, 3, 0, 0, 0)
        resolution = SummaryResolution.day
        labels = list(LabelRange(begin, end, resolution))

    Results in the following list::

        ['2020-01-01', '2020-01-02', '2020-01-03']

    """

    RESOLUTIONS = {
        SummaryResolution.hour: '%Y-%m-%d %H:00',
        SummaryResolution.day: '%Y-%m-%d',
        SummaryResolution.month: '%Y-%m',
        SummaryResolution.year: '%Y',
    }

    LABEL_STEP = {
        SummaryResolution.hour: relativedelta(hours=1),
        SummaryResolution.day: relativedelta(days=1),
        SummaryResolution.month: relativedelta(months=1),
        SummaryResolution.year: relativedelta(years=1),
        SummaryResolution.all: None,
    }

    def __init__(self, begin, end, resolution):
        """
        :param datetime begin:
        :param datetime end:
        :param SummaryResolution resolution:
        """
        self.begin = begin
        self.end = end
        self.resolution = resolution

    def __iter__(self):
        return iter(self.get_label_range())

    def get_label_range(self):
        format = self.RESOLUTIONS[self.resolution]
        step = self.LABEL_STEP[self.resolution]
        begin = self.begin
        labels = []

        while begin < self.end:
            labels.append(begin.strftime(format))
            begin += step

        return labels
