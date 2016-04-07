#!/usr/bin/env python

import smbus
import time
import string

bus = smbus.SMBus(1) # Rev 2 Pi uses 1
i2c_data=00
i2c_control=00
i2c_adress=0x3e

def writeI2C(cntr, dat):
    try:
	bus.write_byte_data(i2c_adress,cntr,dat)
    	time.sleep(0.003)
    except Exception, e:
    	import traceback  
        print traceback.format_exc()		

def printtext(txt):
    leng = len(txt)
    for a in range(0, leng):
        writeI2C(0x40, ord(txt[a]))

def gotoLine1():
    writeI2C(0x00,0B00000011)
def gotoLine2():
    writeI2C(0x00,0xc0)

def initDisplay():
    writeI2C(0x00,0x00)
    writeI2C(0x00,0x38)
    writeI2C(0x00,0x00)
    writeI2C(0x00,0x39)
    writeI2C(0x00,0x14)
    writeI2C(0x00,0x74)
    writeI2C(0x00,0x54)
    writeI2C(0x00,0x6F)
    writeI2C(0x00,0x0C)
    writeI2C(0x00,0x01)

def writeTime():
    printtext(time.strftime("%H:%M:%S"))

initDisplay()
gotoLine1()
printtext('Hallo Hasi!')
gotoLine2()
printtext('es geht endlich..')

#writeI2C(0x07,0x01)
#writeI2C(0x06,0x99)
#writeI2C(0x00,0x04)
#writeI2C(0x09,0xCC)