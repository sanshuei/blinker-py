from Blinker import *

BUTTON_1 = ('ButtonKey')

Blinker.setMode(BLINKER_WIFI)
Blinker.begin()
Blinker.wInit(BUTTON_1, W_BUTTON)

s_value = 0
on_off = 'on'

if __name__ == '__main__':
    while True:
        Blinker.run()
        
        if Blinker.available() == True:
            BLINKER_LOG('Blinker.readString(): ', Blinker.readString())
            Blinker.print(Blinker.times())
            Blinker.vibrate()
            Blinker.print('millis', millis())            

        if Blinker.button(BUTTON_1):
            Blinker.print('Button pressed!')
        
        Blinker.delay(2000)
