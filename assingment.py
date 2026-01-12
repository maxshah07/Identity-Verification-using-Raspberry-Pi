import os
os.system("sudo pigpiod")
from gpiozero import LED, Buzzer, AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
import random
from time import sleep
import sys
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import Keypad
GPIO.setwarnings(False)
reader = SimpleMFRC522()

import time
import smbus
import subprocess

class CharLCD1602(object):
    def __init__(self):
        # Note you need to change the bus number to 0 if running on a revision 1 Raspberry Pi.
        self.bus = smbus.SMBus(1)
        self.BLEN = 1  # turn on/off background light
        self.PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
        self.PCF8574A_address = 0x3f  # I2C address of the PCF8574A chip.
        self.LCD_ADDR =self.PCF8574_address  
    def write_word(self,addr, data):
        temp = data
        if self.BLEN == 1:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.bus.write_byte(addr ,temp)

    def send_command(self,comm):
        # Send bit7-4 firstly
        buf = comm & 0xF0
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR ,buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(self.LCD_ADDR ,buf)
        # Send bit3-0 secondly
        buf = (comm & 0x0F) << 4
        buf |= 0x04               # RS = 0, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR ,buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(self.LCD_ADDR ,buf)

    def send_data(self,data):
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR ,buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(self.LCD_ADDR ,buf)
        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05               # RS = 1, RW = 0, EN = 1
        self.write_word(self.LCD_ADDR ,buf)
        time.sleep(0.002)
        buf &= 0xFB               # Make EN = 0
        self.write_word(self.LCD_ADDR ,buf)

    def i2c_scan(self):
        cmd = "i2cdetect -y 1 |awk \'NR>1 {$1=\"\";print}\'"
        result = subprocess.check_output(cmd, shell=True).decode()
        result = result.replace("\n", "").replace(" --", "")
        i2c_list = result.split(' ')
        return i2c_list

    def init_lcd(self,addr=None, bl=1):
        i2c_list = self.i2c_scan()
#         print(f"i2c_list: {i2c_list}")
        if addr is None:
            if '27' in i2c_list:
                self.LCD_ADDR = self.PCF8574_address
            elif '3f' in i2c_list:
                self.LCD_ADDR = self.PCF8574A_address
            else:
                raise IOError("I2C address 0x27 or 0x3f no found.")
        else:
            self.LCD_ADDR = addr
            if str(hex(addr)).strip('0x') not in i2c_list:
                raise IOError(f"I2C address {str(hex(addr))} or 0x3f no found.")    
        self.BLEN = bl
        try:
            self.send_command(0x33) # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self.send_command(0x32) # Then initialize to 4-line mode
            time.sleep(0.005)
            self.send_command(0x28) # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self.send_command(0x0C) # Enable display without cursor
            time.sleep(0.005)
            self.send_command(0x01) # Clear Screen
            self.buswrite_byte(self.LCD_ADDR, 0x08)
        except:
            return False
        else:
            return True

    def clear(self):
        self.send_command(0x01) # Clear Screen

    def openlight(self):  # Enable the backlight
        self.bus.write_byte(0x27,0x08)
        self.bus.close()

    def write(self,x, y, str):
        if x < 0:
            x = 0
        if x > 15:
            x = 15
        if y <0:
            y = 0
        if y > 1:
            y = 1
        # Move cursor
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        for chr in str:
            self.send_data(ord(chr))
    def display_num(self,x, y, num):
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        self.send_data(num)


ROWS = 4        # number of rows of the Keypad
COLS = 4        #number of columns of the Keypad
keys =  [   '1','2','3','A',    #key code
            '4','5','6','B',
            '7','8','9','C',
            '*','0','#','D'     ]
rowsPins = [18, 23, 24, 12]     #connect to the row pinouts of the keypad
colsPins = [5, 22, 27, 17]

keypad = Keypad.Keypad(keys,rowsPins,colsPins,ROWS,COLS)
keypad.setDebounceTime(50)

greenLED = LED(16) #pin 
redLED = LED(20) #pin 

bz = Buzzer(21) #pin

my_factory = PiGPIOFactory() 
myGPIO=19
SERVO_DELAY_SEC = 0.001 
myCorrection=0.0
maxPW=(2.5+myCorrection)/1000
minPW=(0.5-myCorrection)/1000
servo =  AngularServo(myGPIO,initial_angle=180,min_angle=0, max_angle=180,min_pulse_width=minPW,max_pulse_width=maxPW,pin_factory=my_factory)

north = 90
west = 180
south = 90
east = 180

test2 = {'north': north, 'west': west, 'south': south, 'east': east}

def RFID():
    '''scan for a tag and then checks if it is the correct one'''
    print("Hold a tag near the reader")
    lcd1602.write(0,0,'Place tag near')
    lcd1602.write(0,1,'the reader')
    while True:
            id, text = reader.read()
            print(id)
            if id == 493984550331:
                print("ID: %s\nText: %s" % (id,text))
                break
            else:
                redLED.on()
                bz.on()
                sleep(0.5)
                bz.off()
                lcd1602.clear()
                lcd1602.write(0,0,'ID: ' + str(id))
                lcd1602.write(0,1,'Not Verified')
                
                sleep(2)
                
                lcd1602.clear()
                lcd1602.write(0,0,'Access Denied')
                
                sleep(2)
                lcd1602.clear()
                redLED.off()
                
    greenLED.on()
    bz.on()
    sleep(0.25)
    bz.off()
    sleep(0.1)
    bz.on()
    sleep(0.25)
    bz.off()
    lcd1602.clear()
    lcd1602.write(0,0,'ID: ' + str(id))
    lcd1602.write(0,1,'Verified')
    
    sleep(2)
    
    lcd1602.clear()
    lcd1602.write(0,0,'Access Granted')
    
    sleep(2)
    lcd1602.clear()
    greenLED.off()
    
    
def KeyPad():
    '''scans for a key presses and then adds the pressed key to a list to then be checked'''
    pin = []
    lcd1602.write(0,0,'Enter PIN:')
    while(True):
        key = keypad.getKey()       
        if(key != keypad.NULL):
            if key == '*':
                pin = []
                
                lcd1602.clear()
                lcd1602.write(0,0,'Pin Cleared')
                lcd1602.write(0,1,'Pin:')
                redLED.on()
                bz.on()
                sleep(0.5)
                bz.off()
                
                sleep(1.5)

                redLED.off()
                lcd1602.clear()
                lcd1602.write(0,0,'Enter PIN:')
                
            elif key == '#':
                lcd1602.clear()
                result = int(''.join(pin))
                
                if result == 1111:
                    lcd1602.write(0,0,'Correct PIN')
                    greenLED.on()
                    bz.on()
                    sleep(0.25)
                    bz.off()
                    sleep(0.1)
                    bz.on()
                    sleep(0.25)
                    bz.off()
                    
                    sleep(1)
                    
                    lcd1602.clear()
                    lcd1602.write(0,0,'Access Granted')
                    
                    sleep(2)

                    greenLED.off()
                    lcd1602.clear()
                    break
                
                else:
                    lcd1602.clear()
                    lcd1602.write(0,0,'Incorrect PIN')
                    redLED.on()
                    bz.on()
                    sleep(0.5)
                    bz.off()
                    
                    sleep(1.5)

                    redLED.off()
                    lcd1602.clear()
                    pin = []
                    lcd1602.write(0,0,'Pin Cleared')
                    lcd1602.write(0,1,'Pin:')
                    
                    sleep(2)
                    
                    lcd1602.clear()
                    lcd1602.write(0,0,'Enter PIN:')

            elif key == 'A' or key == 'B' or key == 'C' or key == 'D':
                pin = []
                lcd1602.clear()
                lcd1602.write(0,0,'Invalid number')
                lcd1602.write(0,1,'entered')
                redLED.on()
                bz.on()
                sleep(0.5)
                bz.off()
                
                sleep(1.5)

                redLED.off()
                lcd1602.clear()
                lcd1602.write(0,0,'Pin Cleared')
                lcd1602.write(0,1,'Pin:')
                
                sleep(2)
                
                lcd1602.clear()
                lcd1602.write(0,0,'Enter PIN:')
                    
            else:                
                lcd1602.clear()
                pin.append(key)
                result = int(''.join(pin))
                lcd1602.clear()
                lcd1602.write(0,0,'Enter Pin:' + str(result))
                
                if len(str(result)) == 7:
                    pin = []
                    lcd1602.clear()
                    lcd1602.write(0,0,'Too many numbers')
                    lcd1602.write(0,1,'entered')
                    redLED.on()
                    bz.on()
                    sleep(0.5)
                    bz.off()
                    
                    sleep(1.5)

                    redLED.off()
                    lcd1602.clear()
                    lcd1602.write(0,0,'Pin Cleared')
                    lcd1602.write(0,1,'Pin:')
                    
                    sleep(2)
                    
                    lcd1602.clear()
                    lcd1602.write(0,0,'Enter PIN:')


def Verification():
    '''spins the sevo motor in aa random direction then checks the user input to see if they match'''
    lcd1602.clear()
    lcd1602.write(0,0,'Verification')
    lcd1602.write(0,1,'required')

    sleep(2)

    rorwList = ['red', 'white']

    rorw = random.choice(rorwList)
    print(rorw)

    lcd1602.clear()
    lcd1602.write(0,0,'North faces wires')
    lcd1602.write(0,1,"'#' to continue")

    isCorrect = 'false'

    while(True):    
        key = keypad.getKey()       
        if(key != keypad.NULL):
            if key == '#':
                lcd1602.clear()
                lcd1602.write(0,0,rorw + ' direction?')
                lcd1602.write(0,1,'A=N,B=E,C=S,D=W')

                if rorw == 'red':
                    random2 = random.randint(1,2)
                    if random2 == 1:
                        print('north, red')
                        servo.angle = 90
                        while(True):    
                            key = keypad.getKey()       
                            if(key != keypad.NULL):
                                if key == 'A':
                                    print('okay')
                                    isCorrect = 'true'
                                    break
                                else:
                                    lcd1602.clear()
                                    lcd1602.write(0,0,'Incorrect!')
                                    lcd1602.write(0,1,'Try Again')
                                    redLED.on()
                                    bz.on()
                                    sleep(0.5)
                                    bz.off()

                                    sleep(1.5)

                                    redLED.off()
                                    lcd1602.clear()
                                    lcd1602.write(0,0,rorw + ' direction?')
                                    lcd1602.write(0,1,'A=N,B=E,C=S,D=W')
                    else:
                        print('east, red')
                        servo.angle = 0
                        while(True):    
                            key = keypad.getKey()       
                            if(key != keypad.NULL):
                                if key == 'B':
                                    print('okay')
                                    isCorrect = 'true'
                                    break
                                else:
                                    lcd1602.clear()
                                    lcd1602.write(0,0,'Incorrect!')
                                    lcd1602.write(0,1,'Try Again')
                                    redLED.on()
                                    bz.on()
                                    sleep(0.5)
                                    bz.off()

                                    sleep(1.5)

                                    redLED.off()
                                    lcd1602.clear()
                                    lcd1602.write(0,0,rorw + ' direction?')
                                    lcd1602.write(0,1,'A=N,B=E,C=S,D=W')
                else:
                    random2 = random.randint(1,2)
                    if random2 == 1:
                        print('south, white')
                        servo.angle = 90
                        while(True):    
                            key = keypad.getKey()       
                            if(key != keypad.NULL):
                                if key == 'C':
                                    print('okay')
                                    isCorrect = 'true'
                                    break
                                else:
                                    lcd1602.clear()
                                    lcd1602.write(0,0,'Incorrect!')
                                    lcd1602.write(0,1,'Try Again')
                                    redLED.on()
                                    bz.on()
                                    sleep(0.5)
                                    bz.off()

                                    sleep(1.5)

                                    redLED.off()
                                    lcd1602.clear()
                                    lcd1602.write(0,0,rorw + ' direction?')
                                    lcd1602.write(0,1,'A=N,B=E,C=S,D=W')
                    else:
                        print('west, white')
                        servo.angle = 0
                        while(True):    
                            key = keypad.getKey()       
                            if(key != keypad.NULL):
                                if key == 'D':
                                    print('okay')
                                    isCorrect = 'true'
                                    break
                                else:
                                    lcd1602.clear()
                                    lcd1602.write(0,0,'Incorrect!')
                                    lcd1602.write(0,1,'Try Again')
                                    redLED.on()
                                    bz.on()
                                    sleep(0.5)
                                    bz.off()

                                    sleep(1.5)

                                    redLED.off()
                                    lcd1602.clear()
                                    lcd1602.write(0,0,rorw + ' direction?')
                                    lcd1602.write(0,1,'A=N,B=E,C=S,D=W')

                if isCorrect == 'true':
                    break

                    
    lcd1602.clear()
    lcd1602.write(0,0,'Correct! You')
    lcd1602.write(0,1,'are verified!')

    greenLED.on()
    bz.on()
    sleep(0.25)
    bz.off()
    sleep(0.1)
    bz.on()
    sleep(0.25)
    bz.off()
    
    sleep(3)

    greenLED.off()
    lcd1602.clear()


def destroy():
    '''closes and cleans all components'''
    lcd1602.clear()
    GPIO.cleanup()
    servo.close()
    os.system("sudo killall pigpiod")
    print("Ending program")
    
lcd1602 = CharLCD1602()

if __name__ == '__main__':
    print ('Program is starting ... ')
    lcd1602.init_lcd(addr=None, bl=1)
    try:
        RFID()
        KeyPad()
        Verification()
    except KeyboardInterrupt:
        destroy()

