from os import system
import locale
import pickle
import PySimpleGUI as sg

import Calendar

locale.setlocale(locale.LC_ALL, 'pl_PL.utf8')
sg.theme("DarkAmber")

class App:

    def __init__(self):
        self.calendars = []
        layout = [[sg.Text('Your typed chars appear here:'), sg.Text(size=(15, 1), key='-OUTPUT-')],
                  [sg.Input(key='-IN-')],
                  [sg.Button('Show'), sg.Button('Exit')]]
        window = sg.Window('BudgetApp', layout)
        while True:  # Event Loop
            event, values = window.read()
            print(event, values)
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
            if event == 'Show':
                # Update the "output" text element to be the value of "input" element
                window['-OUTPUT-'].update(values['-IN-'])
        window.close()



    def saveCalendars(self):
        print("Próba zapisu kalendarzy na dysku...")
        pickle.dump(self.calendars, open("calendarsData.pickle", 'wb'))
        print("Zakończono.")

    def loadCalendars(self):
        print("Próba odczytu kalendarzy z dysku...")
        self.calendars = pickle.load(open("calendarsData.pickle", 'rb'))

    def printCalendarNames(self):
        i = 0
        for calendar in self.calendars:
            i += 1
            print("{}. {}".format(i, calendar.cName))


if __name__ == "__main__":
    app = App()
