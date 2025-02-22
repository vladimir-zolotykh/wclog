#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
"""
Add records to pee_diary.db database

Read all logs for one day given at the command line. Duplicated
records are silently overwritten.
"""
import argparse
import argcomplete
import sqlite3
import parse_log_re


class ConnectionDiary(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_tables()

    def make_tables(self):
        self.execute('''
            CREATE TABLE IF NOT EXISTS pee_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pee_time TEXT,
                volume INT DEFAULT 0,
                note TEXT DEFAULT '')
        ''')

    def insert_log(self, pee_time, volume=None, note=''):
        try:
            self.execute('''
                INSERT INTO pee_log (pee_time, volume, note)
                VALUES (?, ?, ?)
            ''', (pee_time, volume, note))
        except sqlite3.IntegrityError as e:
            print(f"SQLite IntegrityError: {e}")


LOG_DB_DEFAULT = "./pee_diary.db"
parser = argparse.ArgumentParser(
    description="Add one day logs to the DB",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('log_file')
parser.add_argument('--log-db', default=LOG_DB_DEFAULT,
                    help='Log database file')
parser.add_argument('--verbose', '-v', action='count', default=0)


def add_diary(log_file, log_db=None):
    """
    Add entries from a log_file to sqlite3 database

    Parameters:
    - log_file: the path to the log file
    - log_db: sqlite3 databse file
    """
    with open(log_file) as fd:
        with sqlite3.connect(log_db, factory=ConnectionDiary) as conn:
            log_str = fd.read()
            parse_res = parse_log_re.parse_log_re(log_str)
            # parse_res: [('24/01/24', ['0220', ..., '0822 473'...])]
            entries = parse_res[0][1]
            # entries  : ['0220', ..., '0822 473'...]
            for (timestamp, rest) in parse_log_re.log_to_timestamps(
                    parse_res[0][0], *entries):
                vol, note = rest
                conn.insert_log(timestamp, vol, note)


if __name__ == '__main__':
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    add_diary(args.log_file, log_db=args.log_db)
