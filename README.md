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
usage: two_report.py [-h] [-d] [--history] [--cookies COOKIES] [-a AUTO]

Automatic doch1. In order for this script to work, you need to login via
chrome/doch1 app (only works for rooted android phones) and choose the "Remember
me" option

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print debug messages
  --history             Show report history
  -c, --cookies COOKIES     Override cookies scan and provied yaml format cookies
                        file
  -a AUTO, --auto AUTO  Auto fill report from file
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

### Auto fill
You can run the program with "--auto" flag and the program will get from this [yaml](https://en.wikipedia.org/wiki/YAML) file the correct date, and fill the status according to that file.
The syntax is:
```yaml
<day>.<month>: "<status>"
```
For example:
```yaml
27.12: "here"
```

### License
----
MIT