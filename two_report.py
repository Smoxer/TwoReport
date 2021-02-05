#!/bin/python3

from urllib.parse import urlparse
from logbook import Logger, RotatingFileHandler, StreamHandler
import argparse
import requests
import sqlite3
import pathlib
import datetime
import schedule
import random
import time
import yaml
import sys
import os

FIREFOX_UA = 'Mozilla/5.0 (Android 11; Mobile; rv:83.0) Gecko/83.0 Firefox/83.0'
SQLITE_COOKIES_LOCATIONS = ['/data/data/il.idf.doch1/app_webview/Default/Cookies',  # Android - root required
                            r'%localappdata%\Google\Chrome\User Data\Default\Cookies',  # Windows
                            '~/Library/Application Support/Google/Chrome/Default/Cookies'  # macOS
                            ]


class OneReport:
    ONE_REPORT_URL = 'https://one.prat.idf.il/'
    CLEARANCE_URL = 'https://clearance.medical.idf.il/'
    ONE_REPORT_ENSURE_LOGIN_URI = 'api/Attendance/GetReportedData'
    ONE_REPORT_ALLOWED_STATUS_URI = 'api/Attendance/GetAllFilterStatuses'
    ONE_REPORT_REPORT_TODAY_URI = 'api/Attendance/InsertPersonalReport'
    ONE_REPORT_HISTORY_URI = 'api/Attendance/memberHistory'
    ONE_REPORT_DEFAULT_KEY = 'default'
    CLEARANCE_REPORT_URI = 'api/report/addReport'
    HEADERS = {'User-Agent': FIREFOX_UA, 'Accept': 'application/json, text/plain, */*'}
    RUNNING_DIR = pathlib.Path(__file__).parent.absolute()

    def __init__(self, cookies_file=None):
        StreamHandler(sys.stdout, bubble=True).push_application()
        RotatingFileHandler(os.path.join(self.RUNNING_DIR, 'OneReport.txt'), max_size=1024 * 1024, backup_count=1,
                            bubble=True).push_application()
        self.user_data = {}
        self.logger = Logger('TwoReport')
        self._allowed_status = {}
        self._session = requests.Session()
        self._session.headers.update(OneReport.HEADERS)
        self._override_cookies(cookies_file)

    def _decrypt_cookie(self, blob):
        if os.name == 'nt':
            try:
                import win32crypt
            except ImportError:
                self.logger.warning("Can't import win32crypt, try to run pip install pywin32")
                return ''
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode('utf-8')
        else:
            self.logger.warning(f"Decrypt strategy wasn't found for {os.name}")
        return ''

    def _get_connection_cookies(self):
        """
        Get connection session from il.idf.doch1 app 
        """
        result = {}
        for sqlite in SQLITE_COOKIES_LOCATIONS:
            sqlite = os.path.expandvars(sqlite)
            if os.path.exists(sqlite):
                self.logger.debug(f'Found matching SQLITE db at {sqlite}')
                connection = sqlite3.connect(sqlite)
                cursor = connection.cursor()
                sql_query = "SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE '%prat.idf.il%';"
                for row in cursor.execute(sql_query):
                    key = row[0]
                    value = row[1]
                    encrypted_value = row[2]
                    if value == '':
                        if encrypted_value != '':
                            value = self._decrypt_cookie(encrypted_value)
                        else:
                            self.logger.warning(f'Cookie {key} is empty')
                    result[key] = value
        return result

    def _get_cookies_from_file(self, cookies_file_path):
        if os.path.exists(cookies_file_path):
            self.logger.debug(f'Getting cookies from {cookies_file_path}')
            with open(cookies_file_path, 'rb') as cookies_fd:
                return yaml.safe_load(cookies_fd)
        self.logger.warning(f'File {cookies_file_path} was not found!')
        return {}

    def _override_cookies(self, cookies_file):
        if not cookies_file:
            cookies = self._get_connection_cookies()
        else:
            cookies = self._get_cookies_from_file(cookies_file)
        self._session.cookies.update(cookies)
        self.logger.debug(f'Using cookies {cookies}')

    def _ensure_login(self):
        if self.user_data == {}:
            self.logger.warning(f'You must logged in!')
            sys.exit(1)

    def _update_status(self):
        status_request = self._session.get(self.ONE_REPORT_URL + self.ONE_REPORT_ALLOWED_STATUS_URI)
        if status_request.status_code == 200:
            self._allowed_status = status_request.json()
        else:
            self.logger.warning(f"Can't login, got status code {status_request.status_code}")

    def login(self):
        """
        Ensure we are logged in and get our name as a test
        """
        ensure_login_request = self._session.get(self.ONE_REPORT_URL + self.ONE_REPORT_ENSURE_LOGIN_URI)
        if ensure_login_request.status_code == 200:
            self.user_data = ensure_login_request.json()
            self.logger.info(f"Logged in as {self.user_data['firstName']} {self.user_data['lastName']}")
            self._update_status()
        else:
            self.logger.warning(f"Can't login, got status code {ensure_login_request.status_code}")
        self._ensure_login()

    def print_history(self):
        """
        See reports history
        """
        now = datetime.datetime.now()
        payload = {'month': now.month, 'year': now.year}
        history = self._session.post(self.ONE_REPORT_URL + self.ONE_REPORT_HISTORY_URI, json=payload).json()
        for day in history['days']:
            print(f"{day['date']}\t\t{day['mainStatusDeterminedName']} - {day['secondaryStatusDeterminedName']}")

    def report_today(self, main_code, secondary_code, note=''):
        self._ensure_login()
        if self.user_data['cantReport']:
            print(f"Can't report right now")
        elif self.user_data['reported']:
            print('Already reported')
        else:
            payload = {'MainCode': (None, str(main_code).zfill(2)),
                       'SecondaryCode': (None, str(secondary_code).zfill(2)), 'Note': (None, str(note))}
            report_request = self._session.post(self.ONE_REPORT_URL + self.ONE_REPORT_REPORT_TODAY_URI,
                                                files=payload).json()
            if report_request:
                self._update_status()
                print(f"Reported {self.user_data['mainTextReported']} - {self.user_data['secondaryTextReported']} "
                      f"on {self.user_data['firstName']} {self.user_data['lastName']}")
            else:
                self.logger.error("Can't report")

    def _report_by_priority(self, reports):
        reports = {str(key).lower(): value for key, value in reports.items()}
        now = datetime.datetime.now()
        specific_day = f'{now.day}.{now.month}'
        day_name = now.strftime("%A").lower()
        date_option = None

        if specific_day in reports:
            date_option = specific_day
        elif day_name in reports:
            date_option = day_name
        elif self.ONE_REPORT_DEFAULT_KEY in reports:
            date_option = self.ONE_REPORT_DEFAULT_KEY
        else:
            self.logger.error('No option specified for today')

        if date_option:
            report_self = reports[date_option]['report_self']
            note = ''
            main_code = report_self['main_code']
            secondary_code = report_self['secondary_code']
            if 'note' in report_self:
                note = report_self['note']
            print(f"Reporting {reports[date_option]} on today (option: {date_option})")
            self.report_today(main_code, secondary_code, note)

    def _read_yml_file(self, path):
        if not os.path.exists(path):
            self.logger.error(f'File {path} does not exists!')
            sys.exit(1)
        with open(path, 'rb') as yml_data:
            result = yaml.safe_load(yml_data)
        return result

    def auto_report_from_file(self, report_file_path):
        self.login()
        self._ensure_login()
        if self.user_data['cantReport']:
            self.logger.warning(f"Can't report right now")
        else:
            self._report_by_priority(self._read_yml_file(report_file_path))

    def print_report_list(self):
        for primary in self._allowed_status['primaries']:
            print(f"{primary['statusCode']} - {primary['statusDescription']}")
            for secondary in primary['secondaries']:
                print(f"\t{secondary['statusCode']} - {secondary['statusDescription']}")

    def report_clearance(self, headers_path):
        headers = self._read_yml_file(headers_path)
        payload = {'isSymptom': False, 'isProximity': False, 'potentialAnswers':
            {'isFever': False, 'isAllergy': False, 'isFluVaccine': False}
        }
        report_request = self._session.post(self.CLEARANCE_URL + self.CLEARANCE_REPORT_URI,
                                            json=payload, headers=headers)
        if report_request.status_code == 200:
            print(f"Clearance reported on {report_request.json()['reportUpdatedDate']}")
        else:
            self.logger.error("Can't report")


def parse_args():
    parser = argparse.ArgumentParser(description='Automatic doch1. In order for this script to work, you need to '
                                                 'login via chrome/doch1 app (only works for rooted android phones) '
                                                 'and choose the "Remember me" option')
    parser.add_argument('--history', action='store_true',
                        help='Show report history')
    parser.add_argument('-c', '--cookies', action='store',
                        help='Override cookies scan and provied yaml format cookies file')
    parser.add_argument('-a', '--auto', action='store',
                        help='Auto fill report from file')
    parser.add_argument('-l', '--report_list', action='store_true',
                        help='Show report options list')
    parser.add_argument('-d', '--daemonize', action='store_true',
                        help='Run the program as daemon')
    parser.add_argument('-e', '--clearance', type=str, default=None,
                        help='Path for headers yml (in order to run auth for clearance)')
    parser.add_argument('-r', '--run_hour', type=int, default=8,
                        help="Run the cron at the specific hour (24 hours format)")
    return parser.parse_args()


def main():
    args = parse_args()
    one_report = OneReport(args.cookies)

    if args.history:
        one_report.login()
        one_report.print_history()
    elif args.report_list:
        one_report.login()
        one_report.print_report_list()
    elif args.daemonize and not args.auto:
        one_report.logger.error('"--daemonize" must run with "--auto"')
    elif args.auto:
        if args.daemonize:
            run_time = f'{str(args.run_hour).zfill(2)}:{str(random.randrange(0, 59)).zfill(2)}'
            schedule.every().day.at(run_time).do(one_report.auto_report_from_file, args.auto)
            if args.clearance:
                schedule.every().day.at(run_time).do(one_report.report_clearance, args.clearance)
            while True:
                schedule.run_pending()
                time.sleep(60)
        else:
            one_report.auto_report_from_file(args.auto)
            if args.clearance:
                one_report.report_clearance(args.clearance)
    else:
        print(f'Nothing to do')


if __name__ == '__main__':
    main()
