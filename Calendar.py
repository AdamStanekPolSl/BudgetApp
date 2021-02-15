from __future__ import print_function
import re
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Calendar:
    creds = None
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    service = None

    def __init__(self):
        self.cName = None
        self.hourlyRate = float
        self.calendarList = None
        self.events = []
        self.hoursWorked = 0.0
        self.income = 0.0
        self.averageHourlyRate = 0.0
        self.changeHourlyRate()
        self.connectToGoogleApi()
        self.updateCalendarList()
        self.printCalendarList()
        n = int(input("Podaj numer kalendarza: "))
        self.addEventsFromCalendar(self.getCalendarId(n))
        self.updateWageOfCalendar()
        print("Pomyślnie utworzono kalendarz {}.".format(self.cName))

    def updateCalendarList(self):
        print("Pobieranie kalendarzy z konta...")
        try:
            response = self.service.calendarList().list().execute()
            self.calendarList = response["items"]
        except:
            print("Błąd podczas pobierania kalendarzy.")

    def countAverageHourlyRate(self):
        try:
            self.averageHourlyRate = self.income/self.hoursWorked
        except:
            self.averageHourlyRate = 0.0
            print("Błąd podczas obliczania średniej stawki godzinowej.\n"
                  "Przypisano {} zł/h.".format(self.averageHourlyRate))

    def printMonthStatistics(self, month):  #month as int [0,...,11]
        mIncome = 0.0
        mHours = 0.0
        for event in self.events[month]:
            mIncome += event["wage"]
            mHours += event["hours"]
        try:
            mAverageHourlyRate = mIncome / mHours
        except:
            mAverageHourlyRate = 0.0
        print("W tym miesiącu:\nDochód - {} zł\nGodzin - {} h\nStawka - {} zł/h".format(mIncome, mHours,
                                                                                        mAverageHourlyRate))

    def getDurationTimeOfEvent(self, event):
        hours = 1.0
        try:
            eventStart = event["start"]
            eventEnd = event["end"]
            if not eventStart.get("dateTime"):
                hours = 24.0
            else:
                eventStart = datetime.datetime.strptime(eventStart["dateTime"].replace(":", ""), "%Y-%m-%dT%H%M%S%z")
                eventEnd = datetime.datetime.strptime(eventEnd["dateTime"].replace(":", ""), "%Y-%m-%dT%H%M%S%z")
                duration = eventEnd - eventStart
                hours = duration.total_seconds() / 3600.0
        except:
            print("Błąd przy obliczaniu czasu trwania wydarzenia. Przyjęto domyślny czas 1.0 h.")
        return hours

    def countWageOfEvent(self, event):
        event["hourlyRate"] = self.hourlyRate
        wage = 0.0
        hours = self.getDurationTimeOfEvent(event)
        value = re.search('\d+\s[Zz][lłLŁ]', event["summary"])
        # Find custom wage in name('summary') of event ex. 60 zł
        if value:
            pln = 0.
            try:
                pln = float(re.search('\d+', value.group()).group())
                if re.search('\d+\s[Zz][lłZŁ]/h', event["summary"]):
                    event["hourlyRate"] = pln
                    wage = hours * event["hourlyRate"]
                else:
                    wage = pln
                    event["hourlyRate"] = wage / hours
            except:
                print("Podczas obliczania stawki niestandardowej wystąpił błąd.\n"
                      "value = {}".format(pln))
        else:
            wage = hours * self.hourlyRate
        event["wage"] = wage
        event["hours"] = hours
        self.hoursWorked = self.hoursWorked + hours
        self.income = self.income + wage

    def updateWageOfCalendar(self):
        for month in range(0, 12, 1):
            for event in self.events[month]:
                self.countWageOfEvent(event)

    def changeHourlyRate(self):
        while True:
            try:
                self.hourlyRate = float(input("Podaj stawkę godzinową dla tego kalendarza: "))
                if self.hourlyRate > 0.:
                    break
            except:
                print("Nie można ustawić stawki jako {}. Ponów próbę.")

    def addEventsFromCalendar(self, calId):
        for i in range(1, 13, 1):
            j = i + 1
            year = datetime.datetime.today().year
            startTime = datetime.datetime(year, i, 1, 00, 00, 00).isoformat() + 'Z'
            if i == 12:
                year += 1
                j = 1
            endTime = datetime.datetime(year, j, 1, 00, 00, 00).isoformat() + 'Z'
            response = self.service.events().list(calendarId=calId,
                                                  timeMin=startTime,
                                                  timeMax=endTime,
                                                  orderBy="updated",
                                                  maxResults=2500).execute()
            self.events.append(response["items"])

    def getCalendarId(self, number):
        number -= 1
        self.cName = self.calendarList[number]["summary"]
        return self.calendarList[number]['id']

    def printCalendarList(self):
        print("Wczytane kalendarze:")
        i = 0
        for calendarListEntry in self.calendarList:
            i += 1
            print("{}. {}".format(i, calendarListEntry['summary']))

    def printEventsList(self):
        print("Wczytane wydarzenia:")
        for j in range(0, 12, 1):
            month = datetime.date(9999, j+1, 1).strftime('%B')
            print("Miesiąc {}:".format(month))
            i = 0
            for event in self.events[j]:
                i += 1
                print("{}. {}\t{} zł/h\t{} h\t{} zł".format(i, event["summary"], event["hourlyRate"],
                                                            event["hours"], event["wage"]))
            self.printMonthStatistics(j)
        print("Czas pracy - {} h\nDochód - {} zł\nStawka - {} zł/h".format(self.hoursWorked, self.income, self.income/self.hoursWorked))

    def connectToGoogleApi(self):
        print("Próba połączenia z https://www.googleapis.com/auth/calendar.readonly...")
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        self.service = build('calendar', 'v3', credentials=self.creds)
