from Blinker import *

BUTTON_1 = ('ButtonKey')

Blinker.setMode(BLINKER_WIFI)
Blinker.begin()
Blinker.wInit(BUTTON_1, W_BUTTON)

if __name__ == '__main__':
    while True:
        if Blinker.available() == True:
            BLINKER_LOG('Blinker.readString(): ', Blinker.readString())
            Blinker.print(Blinker.times())
            Blinker.vibrate()
            Blinker.print('millis', millis())            

        if Blinker.button(BUTTON_1):
            Blinker.print('Button pressed!')
            Blinker.notify('!Button pressed!')

        Blinker.delay(2000)