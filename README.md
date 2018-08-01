# auto-scheduler

Creates events in google calendar for your upcoming classes.
Dependent on [GradeForge](https://github.com/jyn514/GradeForge/)

## Installing
- Run `git clone https://github.com/jyn514/gradeforge`
- Run `pip install -r requirements.txt`
- See [Google's API docs](https://developers.google.com/calendar/quickstart/python)
for info on how to set up the calendar API.
- With GradeForge installed, run `ln /path/to/gradeforge/classes.sql`

## Usage
```
usage: main.py [-h] [--no-auth] [--dry-run] [--debug] courses [courses ...]

positional arguments:
  courses

optional arguments:
  -h, --help  show this help message and exit
  --no-auth   don't authenticate with google; just create the request objects.
              no auth implies dry run
  --dry-run   don't create the events, just show what would happen
  --debug     be verbose
```

## Features
- start and end dates, start and end times
- days of the week
- summaries are department and code; descriptions are the course title
- shows locations
