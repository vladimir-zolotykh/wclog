#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os
from typing import Any, Generator
import re
import argparse
from datetime import datetime
import argcomplete
from logrecord import LogRecord


parser = argparse.ArgumentParser(
    prog='sampletag_re.py',
    description='Parse log file, e.g., LOG_DIARY/2024-01-15.txt',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    'logfile',
    # action='store_const',
    # const='LOG_DIARY/2024-01-15.txt',
    help='The logfile to parse (default: LOG_DIARY/2024-01-15.txt)')


class ParseHeaderError(Exception): pass  # noqa
class ParseSampleError(Exception): pass  # noqa


def parse_date(date_str: str) -> datetime:
    date_str = date_str.strip()
    m = re.match(r'^\d{4}-\d{2}-\d{2}$', date_str)
    if m:
        y, m, d = map(int, date_str.split('-'))
        return datetime(year=y, month=m, day=d)
    else:
        raise ParseHeaderError(
            f'{date_str}: Invalid header line, must be YYYY-MM-DD')


def parse_sample(sample_str: str, sample_date: datetime) -> LogRecord:
    # TODO: modify the following re to match "2400" line.
    m = re.match(r'^(?P<time>\d{3,4})\s+(?P<volume>\d+)?(?P<rest>.*)$',
                 sample_str)
    if m:
        # There's no "note" in YYYY-MM-DD.txt files. To enter it use
        # log_viewer (tk interface).
        time4 = m.group('time')
        if len(time4) < 4:
            time4 = '0' + time4
        time = datetime.strptime(time4, '%H%M').time()
        stamp_str = datetime.combine(sample_date, time).strftime(
            '%Y-%m-%d %H:%M:00')
        label_text = [''] * 3
        tags = re.findall(r'\w+', m.group('rest'))
        for n in range(1, 4):
            try:
                label_text[n] = tags.pop(0)
            except IndexError:
                break
        try:
            volume = int(m.group('volume'))
        except TypeError:
            volume = 0
        rec = LogRecord(
            id=1, stamp=stamp_str,
            label1=label_text[0], label2=label_text[1], label3=label_text[2],
            volume=volume)
        return rec
    else:
        raise ParseSampleError(f'{sample_str.strip()}: Invalid sample line')


def logrecords_generator(logfile: str) -> Generator[LogRecord, Any, None]:
    def startswithany(line, words=('2400', 'Pira', 'headache', 'benchpress',
                                   'IMET', 'Мефенаминка', 'Creatine', 'Кофе',
                                   'душ', 'stool')):
        for w in words:
            if line.upper().startswith(w.upper()):
                return True
        return False

    try:
        fd = open(logfile)
    except FileNotFoundError:
        logfile = os.path.join('LOG_DIARY', logfile)
        fd = open(logfile)
    with fd:
        for line_no, line_str in enumerate(fd, 1):
            # skip empty lines
            if line_str == '\n':
                continue
            if line_no == 1:
                log_datetime = parse_date(line_str)
            else:
                if startswithany(line_str):
                    print(f'{logfile}-{line_no}: {line_str.strip()} '
                          f'- Invalid sample')
                    continue
                yield parse_sample(line_str, log_datetime)


if __name__ == '__main__':
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    for log in logrecords_generator(args.logfile):
        print(repr(log))
