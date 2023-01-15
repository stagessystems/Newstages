from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


def months_between(start_date, end_date):
    # Add 1 day to end date to solve different last days of month
    s1, e1 = start_date, end_date + timedelta(days=1)
    # Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    # Count days between the two 360 dates and return tuple (months, days)
    return float(e360 - s360)/30


def years_between(start_date, end_date):
    # Add 1 day to end date to solve different last days of month
    s1, e1 = start_date, end_date + timedelta(days=1)
    # Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    # Count days between the two 360 dates and return tuple (years, days)
    return float(e360 - s360)/360
