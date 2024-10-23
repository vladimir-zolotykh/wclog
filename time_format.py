#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""
>>> to24H(['125', '411', '538', '710', '804', '931', '1050', '1141',\
           '1244', '102', '129', '200', '223', '242', '300', '331',\
           '351', '437', '520', '643', '752', '952'])
['0125', '0411', '0538', '0710', '0804', '0931', '1050', '1141',\
 '1244', '1302', '1329', '1400', '1423', '1442', '1500', '1531',\
 '1551', '1637', '1720', '1843', '1952', '2152']
"""
from datetime import datetime


def to24H(times: list[str]) -> list[str]:
    times12H: list[str] = times
    times24H: list[str] = []
    sfx = 'AM'
    am0 = datetime.strptime('1200am', '%I%M%p')
    dt: datetime = am0
    for time_str in times12H:
        if len(time_str) <= 3:
            time_str = time_str.zfill(4)
        time_str += sfx
        format = '%I%M%p'
        dt_prev: datetime = dt
        dt = datetime.strptime(time_str, format)
        if dt.hour < dt_prev.hour:
            sfx = 'PM'
            time_str = time_str[:-2] + sfx
            dt = datetime.strptime(time_str, format)
        times24H.append(dt.strftime('%H%M'))
    return times24H


if __name__ == '__main__':
    # convert_12_to_24_hour_format("LOG_DIARY/2024-01-18.txt")
    import doctest
    doctest.testmod()
