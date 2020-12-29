# TwoReport
Two report is automatic one report (https://one.prat.idf.il/).

Capabilities:
- Auto fill one report when running
- With a given list, can auto fill the correct status for each day (when running as daily cron)
- Can show report history

### Installation
```sh
$ git clone https://github.com/Smoxer/TwoReport.git
$ cd TwoReport
$ pip install -m requirements.txt
```

### Running
```
usage: two_report.py [-h] [--history] [-c COOKIES] [-a AUTO] [-l] [-d] [-r RUN_HOUR]

Automatic doch1. In order for this script to work, you need to login via chrome/doch1 app (only works for rooted
android phones) and choose the "Remember me" option

optional arguments:
  -h, --help            show this help message and exit
  --history             Show report history
  -c COOKIES, --cookies COOKIES
                        Override cookies scan and provied yaml format cookies file
  -a AUTO, --auto AUTO  Auto fill report from file
  -l, --report_list     Show report options list
  -d, --daemonize       Run the program as daemon
  -r RUN_HOUR, --run_hour RUN_HOUR
                        Run the cron at the specific hour (24 hours format)
```

### Cookies
You have two options - auto detection for cookies and manual giving cookies.
The "secret" of two report that this is using your cookies in order to log in as your user.
Right now, two report supporting the following auto cookies detections:
- Android devices - Root only! (with [doch1](https://play.google.com/store/apps/details?id=il.idf.doch1) app installed and logged in)
- Windows - Chrome only
- Mac - Chrome only

Alternative, you can supply your own cookies with the "--cookies" flag.
The file should be in [yaml](https://en.wikipedia.org/wiki/YAML) format.
In order to get cookies for the site, you can read [this](https://www.cookieyes.com/how-to-check-cookies-on-your-website-manually/) article for one.prat.idf.il site.

### List options
You can run `two_report.py -l` in order to get the full list.
The first value is the main code, and the tabbed value is the secondary value.
```
01 - נמצא ביחידה
        01 - נוכח
02 - מחוץ ליחידה
        05 - בתפקיד מחוץ ליחידה
        09 - אחרי תורנות \ משמרת
        03 - עובד משמרות
        13 - הפניה רפואית
        16 - משמרת ערב
        02 - אבט"ש
        14 - לימודים על סמך אישור
        18 - הצ"ח
        20 - סבב קו
        23 - יום פרט
04 - חופשה שנתית
        01 - חופשה שנתית
        04 - חופשת אבל - קבע
        06 - חג עדתי
        10 - חופשה ללא תשלום קצרה
        11 - אזכרה - קרבה ראשונה
05 - חופשת מחלה
        01 - חופשת מחלה (גימלים)
        02 - מחלה עפ"י הצהרה
        07 - טיפול רפואי
        03 - מחלת ילד
        04 - מחלת הורה
        16 - שמירת הריון
        05 - מחלת בן\בת זוג
        09 - מחלת ילד ממארת
        10 - מחלת בן זוג ממארת
        11 - הריון או לידת בת זוג
        12 - תרומת מח עצם / איברים
        14 - הורה לבעל מוגבלויות
        15 - מחלה בפציעה בתפקיד
17 - בידוד
        17 - מחלה שנתית
        18 - בידוד ביחידה
        19 - ע"ח חופשה שנתית
        20 - עבודה מהבית
```

### Auto fill
You can run the program with "--auto" flag and the program will get from this [yaml](https://en.wikipedia.org/wiki/YAML) file the correct date, and fill the status according to that file.
You can get the main and secondary codes by running `two_report.py -l`
The syntax is:
```yaml
<day>.<month>: 
  report_self:
    main_code: <MainCode>
    secondary_code: <SecondaryCode>
    note: <FreeText - optional>
```
For example:
```yaml
27.12: 
  report_self:
    main_code: 02
    secondary_code: 05
    note: 'בקורס מקוון'
```

### License
----
MIT