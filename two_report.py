#!/bin/python3

from urllib.parse import urlparse
import argparse
import requests
import sqlite3
import warnings
import datetime
import yaml
import sys
import os

FIREFOX_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'
SQLITE_COOKIES_LOCATIONS = ['/data/data/il.idf.doch1/app_webview/Default/Cookies', # Android - root required
                            r'%localappdata%\Google\Chrome\User Data\Default\Cookies', # Windows
                            '~/Library/Application Support/Google/Chrome/Default/Cookies' # macOS
                            ]


class OneReport:
    ONE_REPORT_URL = 'https://one.prat.idf.il/'
    ENSURE_LOGIN_URI = 'api/Attendance/GetReportedData'
    REPORT_TODAY_URI = ''
    HISTORY_URI = 'api/Attendance/memberHistory'
    FINISH_URI = 'finish'
    HEADERS = {'User-Agent': FIREFOX_UA, 'Accept': 'application/json, text/plain, */*', 'Host': urlparse(ONE_REPORT_URL).netloc}

    def __init__(self, debug=False, cookies_file=None):
        self.user_data = {}

        self._debug = debug
        self._session = requests.Session()
        self._session.headers.update(OneReport.HEADERS)
        self._override_cookies(cookies_file)
        self._keepalive()

    def _keepalive(self):
        '''
        Sending keepalive to the server in order to extend our session
        '''
        self._log('Sending keepalive')
        self._session.get(self.ONE_REPORT_URL + self.FINISH_URI)

    def _log(self, message, stdout_func=print):
        if self._debug or stdout_func != print:
            stdout_func(message)

    def _decrypt_cookie(self, blob):
        if os.name == 'nt':
            try:
                import win32crypt
            except ImportError:
                self._log("Can't import win32crypt, try to run pip install pywin32", warnings.warn)
                return ''
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode('utf-8')
        else:
            self._log(f"Decrypt strategy wasn't found for {os.name}", warnings.warn)
        return ''

    def _get_connection_cookies(self):
        '''
        Get connection session from il.idf.doch1 app 
        '''
        result = {}
        for sqlite in SQLITE_COOKIES_LOCATIONS:
            sqlite = os.path.expandvars(sqlite)
            if os.path.exists(sqlite):
                self._log(f'Found matching SQLITE db at {sqlite}')
                connection = sqlite3.connect(sqlite)
                cursor = connection.cursor()
                for row in cursor.execute("SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE '%prat.idf.il%';"):
                    key = row[0]
                    value = row[1]
                    encrypted_value = row[2]
                    if value == '':
                        if encrypted_value != '':
                            value = self._decrypt_cookie(encrypted_value)
                        else:
                            self._log(f'Cookie {key} is empty', warnings.warn)
                    result[key] = value
        return result

    def _get_cookies_from_file(self, cookies_file_path):
        if os.path.exists(cookies_file_path):
            self._log(f'Getting cookies from {cookies_file_path}')
            with open(cookies_file_path, 'rb') as cookies_fd:
                return yaml.safe_load(cookies_fd)
        self._log(f'File {cookies_file_path} was not found!', warnings.warn)
        return {}

    def _override_cookies(self, cookies_file):
        if not cookies_file:
            cookies = self._get_connection_cookies()
        else:
            cookies = self._get_cookies_from_file(cookies_file)
        self._session.cookies.update(cookies)
        self._log(f'Using cookies {cookies}')

    def _ensure_login(self):
        if self.user_data == {}:
            self._log(f'You must logged in!', warnings.warn)

    def login(self):
        '''
        Ensure we are logged in and get our name as a test
        '''
        ensure_login_request = self._session.get(self.ONE_REPORT_URL + self.ENSURE_LOGIN_URI)
        if ensure_login_request.status_code == 200:
            self.user_data = ensure_login_request.json()
            print(f"Logged in as {self.user_data['firstName']} {self.user_data['lastName']}")
        else:
            self._log(f"Can't login, got status code {ensure_login_request.status_code}")

    def print_history(self):
        '''
        See reports history
        '''
        now = datetime.datetime.now()
        history = self._session.post(self.ONE_REPORT_URL + self.HISTORY_URI, json={'month': now.month, 'year': now.year}).json() 
        for day in history['days']:
            print(f"{day['date']}\t\t{day['mainStatusDeterminedName']} - {day['secondaryStatusDeterminedName']}")

    def auto_report_from_file(self, report_file_path):
        self._ensure_login()
        if self.user_data['cantReport']:
            print(f"Can't report right now")
        else:
            if not os.path.exists(report_file_path):
                self._log(f'File {report_file_path} does not exists!', warnings.warn)
                sys.exit(1)
            with open(report_file_path, 'rb') as dates_report:
                reports = yaml.safe_load(dates_report)
            now = datetime.datetime.now()
            current_day = float(f'{now.day}.{now.month}')
            if current_day not in reports:
                self._log(f"Can't find a report for {current_day}", warnings.warn)
            else:
                print(f"Reporting {reports[current_day]} on today ({current_day})")

def parse_args():
    parser = argparse.ArgumentParser(description='Automatic doch1. In order for this script to work, you need to login via chrome/doch1 app (only works for rooted android phones) and choose the "Remember me" option')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug messages')
    parser.add_argument('--history', action='store_true', help='Show report history')
    parser.add_argument('-c', '--cookies', action='store', help='Override cookies scan and provied yaml format cookies file')
    parser.add_argument('-a', '--auto', action='store', help='Auto fill report from file')
    return parser.parse_args()


def main():
    args = parse_args()
    one_report = OneReport(args.debug, args.cookies)
    one_report.login()
    if one_report.user_data == {}:
        sys.exit(1)

    if args.history:
        one_report.print_history()
    elif args.auto:
        one_report.auto_report_from_file(args.auto)
    else:
        print(f'Nothing to do')

if __name__ == '__main__':
    main()
