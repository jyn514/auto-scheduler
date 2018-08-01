#!/usr/bin/env python

from datetime import datetime
from functools import partial
from sqlite3 import connect

from pytz import timezone, utc
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file as oauth_file, client, tools

def run_auth():
    # Setup the Calendar API
    SCOPES = 'https://www.googleapis.com/auth/calendar'
    store = oauth_file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('calendar', 'v3', http=creds.authorize(Http()))


def dictfetchall(cursor):
    'https://stackoverflow.com/a/16523148'
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def query_sections(ids):
    sql = """
    SELECT startDate, startTime, endTime, endDate, days, location,
        title, class.department, section.code
    FROM section INNER JOIN term ON section.term = term.id
                INNER JOIN class ON class.department = section.department
                                    AND class.code = section.code
    WHERE section.uid IN (%s) AND semester = 201808
        -- bad data
        AND class.department NOT IN ('ELCT', 'EDCE')
    """ % ', '.join('?' * len(ids))
    print(sql.replace('?', '%d') % tuple(ids))
    with connect('classes.sql') as connection:
        return dictfetchall(connection.cursor().execute(sql, ids))


# https://tools.ietf.org/html/rfc5545#section-3.3.10
def rfc5545(days, endDate):
    rfc_days = {
        'U': 'SU',
        'M': "MO",
        "T": "TU",
        "W": "WE",
        "R": "TH",
        "F": "FR",
        "S": "SA"
    }
    days = ','.join(rfc_days[day] for day in days)
    # https://github.com/dateutil/dateutil/blob/master/dateutil/rrule.py#L722
    until = endDate.strftime('%Y%m%dT%H%M%SZ')
    return "RRULE:FREQ=WEEKLY;BYDAY=%s;UNTIL=%s" % (days, until)


def parse_time(date, time):
    date_format = '%Y-%m-%d %H:%M'
    eastern = timezone('America/New_York')
    dt = datetime.strptime(date + ' ' + time, date_format)
    return eastern.localize(dt).astimezone(utc)

def format_events(sections):
    events = []
    for event in sections:
        startTime = parse_time(event['startDate'], event['startTime'])
        endTime = parse_time(event['startDate'], event['endTime'])
        endDate = parse_time(event['endDate'], event['endTime'])

        events.append({
            'start': {
                'dateTime': startTime.isoformat(),
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': endTime.isoformat(),
                'timeZone': 'America/New_York'
            },
            'recurrence': [rfc5545(event['days'], endDate)],
            'location': event['location'],
            'description': event['title'],
            'summary': event['department'] + ' ' + event['code'],
        })
    return events


def main(courses, auth=True, dry_run=False):
    if not auth:
        dry_run = True
    else:
        insert = run_auth().events().insert
        print('authentication succeeded')
    sections = query_sections(courses)
    events = format_events(sections)
    for event in events:
        print(event)
        if not dry_run:
            event = insert(calendarId='primary', body=event).execute()
            print('Event created:', event.get('htmlLink'))


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('courses', nargs='*',
                        default=[16290, 12625, 22890, 20997, 16717])
    parser.add_argument('--no-auth', action='store_false', dest='auth',
                        default=True, help="don't authenticate with google; just create the requests; no auth implies dry run")
    parser.add_argument('--dry-run', action='store_true',
                        help="don't create the events, just show what would happen")
    args = parser.parse_args()
    main(**args.__dict__)
