from thread import start_new_thread

#for adc MCP
from ABE_DeltaSigmaPi import DeltaSigma
from ABE_helpers import ABEHelpers
import weather
#import display
import mysql
from subprocess import call     #used for calling MPG123 to speak out text
from PWM_Driver import PWM
import time
import random
import os
import alsaaudio
import RPi.GPIO as GPIO
import math

#RPCServer
from SimpleXMLRPCServer import SimpleXMLRPCServer

class MyRPCFuncs:
    def get_RGBW(self):
        global RGBW
        return RGBW

    def set_operation_mode(self, op_mode):
        global operation_mode
        global startwert
        global maxwert

        operation_mode= op_mode
        print ("mode: %s" % (op_mode))
        return done

    def get_ADC(self, Channel):
        global ADC_result
        return ADC_result[Channel]
    
    def get_door_is_open(self):
        return door_is_open

    def switch_Relais(self, Channel, status):
        switch_Relais(Channel, status)
        return True

    def get_Weather(self):
        return weather.get_weather()

    def get_PWM_Werte(self):
        global PWM_Werte_ist
        return PWM_Werte_ist

    def set_PWM_Werte(self, werte):
        global PWM_Werte_soll
        global operation_mode
        operation_mode="manual"
        print werte
        PWM_Werte_soll=werte
        return "done"

    def get_all_ADC(self):
        global ADC_current_value
        return ADC_current_value

    def hello(self):
        return 'Hello' 

    def div(self, x, y):
        return x // y

    def add(self,x,y):
        return x + y

    def set_PWM(self,channel, a, b):
        rgb.setPWM(channel, a, b)
        return "done"

    def set_volume(value):
        m = alsaaudio.Mixer('PCM', 0)   # defined alsaaudio.Mixer to change volume
        m.setvolume(value) # set volume

    def speak_weather(self):
        MyRPCFuncs.set_volume(100)
        text=weather.get_weather()
        call(["mpg123","-q","http://api.voicerss.org/?key=add015f1fdfd41c69a135c7c9b0025df&src=%s&hl=de-de&f=44khz_16bit_mono" % text])
        #MyRPCFuncs.set_volume(0)

    def speak(self, text):
        MyRPCFuncs.set_volume(100)
        call(["mpg123","-q","http://api.voicerss.org/?key=add015f1fdfd41c69a135c7c9b0025df&src=%s&hl=de-de&f=44khz_16bit_mono" % text])
        #MyRPCFuncs.set_volume(0)

def RPC_Server():
	# Create server
    while (True):
        try:
            server = SimpleXMLRPCServer(("192.168.1.200", 2346)) #, requestHandler=RequestHandler)
            server.register_introspection_functions()   #Registers the XML-RPC introspection functions system.listMethods, system.methodHelp and system.methodSignature.
            server.register_instance(MyRPCFuncs())
            print "waiting for commands"
            server.serve_forever()
        except Exception, e:
            import traceback  
            write_to_log(traceback.format_exc())


def write_to_log(text):
    print text + "\r\n"
    #errorlog = open("/home/pi/log.buch", 'a')
    #errorlog.write("%s - %s \n" % (time.strftime("%Y-%m-%d %H:%M:%S"), text))
    #errorlog.close() 

piano_on_count=0
piano_off_count=0

def Read_all_ADCs():
    try:
        global piano_off_count
        global piano_on_count
        global ADC_Channel
        global ADC_conversions_per_minute
        global ADC_conversion_Minute
        global ADC_result
        global ADC_conversions
        global ADC_current_value
        global PIANO_ON
        current_Minute = time.strftime("%M")

        #print "ADC Minute %s / current Minute %s" % (ADC_conversion_Minute, current_Minute)
        if ADC_conversion_Minute == current_Minute:
            value = adc12.read_voltage(ADC_Channel)
            ADC_current_value[ADC_Channel-1] = value
            ADC_conversions[ADC_Channel-1] += value
            ADC_conversions_per_minute[ADC_Channel-1] += 1
            if ADC_Channel == 2:
                #print ("Piano ADC=%s" % value)
                if value>0.1 and value<1.95:
                    piano_on_count+=1
                    piano_off_count=0
                    if piano_on_count>=5:
                        piano_on_count=0 
                        PIANO_ON=True
                        #print PIANO_ON
                else:	
                    piano_off_count+=1
                    piano_on_count=0
                    if piano_off_count>25: 
                        piano_off_count=0                        
                        PIANO_ON=False
                        #print PIANO_ON

            ADC_Channel = ADC_Channel + 1
          
            if ADC_Channel>4:
                ADC_Channel=1
                if  ADC_result==[0,0,0,0,0,0,0,0]:
                     for Channel in range(0, 7):
                        ADC_result[Channel]=ADC_conversions[Channel]
        else:   #bei neuer Minute durchschnitt berechnen und alles zurücksetzen
            ADC_conversion_Minute=current_Minute
            for Channel in range(0, 7):
                if ADC_conversions_per_minute[Channel]>1:
                    ADC_result[Channel]=ADC_conversions[Channel] / ADC_conversions_per_minute[Channel]
            ADC_conversions_per_minute = [0,0,0,0,0,0,0,0]
            ADC_conversions=[0,0,0,0,0,0,0,0]
            ADC_Channel=0
            if ADC_result != [0,0,0,0,0,0,0,0]:
                write_ADC_to_DB(ADC_result) #insert row to Database

    except Exception, e:
            import traceback  
            write_to_log(traceback.format_exc())

def switch_Relais(nummer, status):
    if nummer == 1:     #12V
        nummer = 38 
    elif nummer == 2:   #halogen
        nummer = 40
    elif nummer == 3:   #aquarium
        nummer = 35
    elif nummer == 4:   #eiszapfen
        nummer = 36
    else: 
        return

    if status == True:
        status=False
    else:
        status=True

    GPIO.output(nummer, status) #true = aus

operation_mode="auto"
startwert=0.17   #helligkeitswert um Licht einzuschalten
maxwert=1500    #pwm wert 0-4095
max_PWM_for_Aquawhite=700

def set_PWM():
    global RGBW
    global PWM_Werte_soll
    global operation_mode
    global startwert
    global maxwert
    global werte
    global AussenHelligkeit
    global PIANO_ON
    global max_PWM_for_Aquawhite
    global door_is_open
#00 carpe oben
#01 carpe unten
#02 aqua oben
#03 aqua unten
#04 regal klavier fenster
#05 Regal carpe + Lade
#06 Piano
#07 TV
#08 halogen
#09 Rattenlicht
#10 Aquarium FAN
#11 Aquarium R
#12 Aquarium G
#13 Aquarium B
#14 Aquarium W

#region "Rattenlicht"
    Ratten_licht=0
    start_fuer_ratten=0.4
    if AussenHelligkeit<start_fuer_ratten:
        if int(time.strftime("%H"))>=14 and int(time.strftime("%H"))<21:
            Ratten_licht=int((maxwert / start_fuer_ratten) * (start_fuer_ratten-AussenHelligkeit))
        elif int(time.strftime("%H"))==21 and int(time.strftime("%M"))<30:
            Ratten_licht=int(((maxwert / start_fuer_ratten) * (start_fuer_ratten-AussenHelligkeit))/2)
            
    PWM_Werte_soll[9]=Ratten_licht

#Licht im aquarium
    e=math.log1p(1024)

    if int(time.strftime("%H"))>=5 and int(time.strftime("%H"))<22:
        PWM_Werte_soll[11]=RGBW[0]
        PWM_Werte_soll[12]=RGBW[1]
        PWM_Werte_soll[13]=RGBW[2]
    else:
        PWM_Werte_soll[11]=0
        PWM_Werte_soll[12]=0
        PWM_Werte_soll[13]=0 
    angepasste_AussenHelligkeit=AussenHelligkeit        
    if AussenHelligkeit<0.0075:
        angepasste_AussenHelligkeit=0

    if int(time.strftime("%H"))>6 and int(time.strftime("%H"))<21:
        if angepasste_AussenHelligkeit>=1:
            PWM_Werte_soll[14]=0
        elif angepasste_AussenHelligkeit>0 and angepasste_AussenHelligkeit<1:
            #weis=1024/e*math.log1p((AussenHelligkeit)*1000)
            #weis=4095/(AussenHelligkeit*1000)
            weis=705-(angepasste_AussenHelligkeit*700)
                
            if weis>695:
                weis=800
            #weis = int(weis / 4095 * max_PWM_for_Aquawhite)
                                
            #print ("draussen: %s weis: %s weis_ist: %s door_open: %s" % (angepasste_AussenHelligkeit*1000, weis, PWM_Werte_ist[14], door_is_open))
            PWM_Werte_soll[14]=int(weis)
    else:   #licht aus
        PWM_Werte_soll[14]=max_PWM_for_Aquawhite    




    if operation_mode=="manual":
        operation_mode=operation_mode
        #do nothing
    elif operation_mode=="auto":
                    

        #autolicht
        if someone_home and door_is_open:
            helligkeit_nach_aussen_licht=int((maxwert / startwert) * (startwert-AussenHelligkeit))
                       
            #print AussenHelligkeit
            #print helligkeit_nach_aussen_licht
            if AussenHelligkeit == 0:
                return 0

            LEDoben=0
            LEDunten=0
            LEDregal=0        
            #print AussenHelligkeit
            if AussenHelligkeit<startwert:
                if int(time.strftime("%H"))>=5 and int(time.strftime("%H"))<8 and int(time.strftime("%w"))>=1 and int(time.strftime("%w"))<=5:
                    LEDregal = int(helligkeit_nach_aussen_licht/4)
                    LEDoben = LEDregal
                    LEDunten = LEDoben*3
                elif int(time.strftime("%H"))>=15 and int(time.strftime("%H"))<19:
                    LEDregal = helligkeit_nach_aussen_licht
                    LEDoben = LEDregal
                    LEDunten = LEDoben/3
                elif int(time.strftime("%H"))>=19 and int(time.strftime("%H"))<20:
                    LEDregal = helligkeit_nach_aussen_licht
                    LEDoben = int(helligkeit_nach_aussen_licht*2/3)
                    LEDunten = LEDoben/3
                elif int(time.strftime("%H"))==20:
                    abdunkelfaktor = int(time.strftime("%M"))*100/60 #blendet jede minute etwas ab
                    LEDregal = int(helligkeit_nach_aussen_licht)
                    LEDoben = int(helligkeit_nach_aussen_licht * 2/3 * (100-abdunkelfaktor)/100)
                    LEDunten = int(helligkeit_nach_aussen_licht/5)
                elif int(time.strftime("%H"))>=21:
                    LEDregal = int(helligkeit_nach_aussen_licht)
                    LEDoben = 0
                    LEDunten =  int(helligkeit_nach_aussen_licht/5)

                #TV Licht
                if PC_is_running:
                    PWM_Werte_soll[7] = helligkeit_nach_aussen_licht
                else:
                    PWM_Werte_soll[7] = 0
                #auto Piano
                if PIANO_ON:
                    PWM_Werte_soll[6] = int( (4095 / startwert) * (startwert-AussenHelligkeit) )
                else:
                    PWM_Werte_soll[6] = 0
            #alle PWM bereinigen
            for PWM_Channel_to_adjust in [0,1,2,3,4,5,8,10,15]:
                PWM_Werte_soll[PWM_Channel_to_adjust]=0
                                          

            #alle PWM auf diesen wert
            #gruppe1
            for PWM_Channel_to_adjust in [4,5]:
                PWM_Werte_soll[PWM_Channel_to_adjust]=LEDregal
            #gruppe2
            for PWM_Channel_to_adjust in [0,2]:
                PWM_Werte_soll[PWM_Channel_to_adjust]=LEDoben
            #gruppe3
            for PWM_Channel_to_adjust in [1,3]:
                PWM_Werte_soll[PWM_Channel_to_adjust]=LEDunten
        else:
            #licht aus
            for PWM_Channel_to_adjust in [0,1,2,3,4,5,6,7,8,10,15]:
                PWM_Werte_soll[PWM_Channel_to_adjust]=0
    
def adjust_PWM():
    global max_PWM_for_Aquawhite
    global PWM_Werte_ist
    global PWM_Werte_soll
    global operation_mode
    waittime = 0.5
    while(True):
        geschwindigkeit=20  #höher ist langsamer
        Relais_on=False
        for PWM_Channel_to_adjust in range(0,15):
            if PWM_Werte_ist[PWM_Channel_to_adjust]!=PWM_Werte_soll[PWM_Channel_to_adjust]:
                if operation_mode=="auto":
                    waittime=0.1
                    if PWM_Channel_to_adjust==14:   #aquarium weis
                        if PWM_Werte_ist[PWM_Channel_to_adjust]>600:
                            changevalue=(abs(PWM_Werte_ist[PWM_Channel_to_adjust] - PWM_Werte_soll[PWM_Channel_to_adjust]))/2
                        else:
                            changevalue=1
                    elif PWM_Channel_to_adjust==6 or PWM_Channel_to_adjust==7:
                        changevalue=1 + (abs(PWM_Werte_ist[PWM_Channel_to_adjust] - PWM_Werte_soll[PWM_Channel_to_adjust]) / geschwindigkeit)
                    else:
                        changevalue=1#+ (abs(PWM_Werte_ist[PWM_Channel_to_adjust] - PWM_Werte_soll[PWM_Channel_to_adjust]) / geschwindigkeit)
                else:
                    waittime=1
                    changevalue=1 + (abs(PWM_Werte_ist[PWM_Channel_to_adjust] - PWM_Werte_soll[PWM_Channel_to_adjust]) / geschwindigkeit)

                if PWM_Werte_ist[PWM_Channel_to_adjust]<PWM_Werte_soll[PWM_Channel_to_adjust]:
                    PWM_Werte_ist[PWM_Channel_to_adjust]+=changevalue
                elif PWM_Werte_ist[PWM_Channel_to_adjust]>PWM_Werte_soll[PWM_Channel_to_adjust]:
                    PWM_Werte_ist[PWM_Channel_to_adjust]-=changevalue
    
            value = PWM_Werte_ist[PWM_Channel_to_adjust]
            if value>0:
                Relais_on=True
            rgb.setPWM(PWM_Channel_to_adjust, 0, value)
        switch_Relais(1, Relais_on)
        #halogen
        if PWM_Werte_ist[8]>0:
            switch_Relais(2, True)
        else:
            switch_Relais(2, False)

        #Aquarium Weis
        if PWM_Werte_ist[14]<max_PWM_for_Aquawhite:    #Relais für licht einschalten
            switch_Relais(3, True)
        else:
            switch_Relais(3, False)
        time.sleep(waittime)

def write_ADC_to_DB(ADC_result):
    global someone_home
    global  DB
    try:
        query="INSERT INTO outside.adc (timestamp,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8, someone_home) VALUES(now()"
        for x in ADC_result:
            query=query + ",'{:0.4f}'".format(x)     
        if someone_home:
            sh="True"
        else:
            sh="False"
        query = query + ", '" + sh + "')"
        #print time.strftime("%H:%M")        
        #print query 
        DB.insert(query)
    except Exception, e:
        DB = mysql.Database()
        DB.insert(query)
        import traceback  
        write_to_log(traceback.format_exc())  

def main_programm():
    
    global werte
    global AussenHelligkeit
    global RGBW
    global DB
    global ADC_result
    global max_PWM_for_Aquawhite
    global door_is_open

    while (True):   #main loop
        try:
            #rgb off
            #rgb.setPWM(0, 0, 4095)
            #rgb.setPWM(1, 0, 4095)
            #rgb.setPWM(2, 0, 4095)
        
            #rgb test
            #for b in range(9, 14):
            #    print b
            #    for a in range(0, 4095,10):
            #        rgb.setPWM(b, 4095, a)
            #    for a in range(0, 4095,10):
            #        rgb.setPWM(b, 4095, 4095-a)

            #display.initDisplay()
            #wettertext = weather.get_weather()
            #speak(wettertext)
            #display.printtext(wettertext)

            while (True):
                try:
                    zeit = time.strftime("%H:%M:%S")
                    try:
                    # Data retrieved from the table
                        for wert in werte:
                            r=int(wert['R']*4096/256)
                            g=int(wert['G']*4096/256)
                            b=int(wert['B']*4096/256)
                            w=int(wert['W']*4096/256)
                            #AussenHelligkeit=int(wert['W']) #aus datenbank
                            RGBW=[r,g,b,w]
                    except Exception, e:
                        print "no cam info"
                        #import traceback  
                        #write_to_log(traceback.format_exc())     

                    try:
                        AussenHelligkeit=ADC_result[0]  #von sensor
                        set_PWM()
                        Read_all_ADCs()
                        door_is_open=not GPIO.input(37)
                        time.sleep(0.1)
                    except Exception, e:
                        import traceback  
                        write_to_log(traceback.format_exc())        	        
                    
                except Exception, e:
                    import traceback  
                    write_to_log(traceback.format_exc())
                    time.sleep(3)
            #  finally:

            DB.close()
        except Exception, e:
            import traceback  
            write_to_log(traceback.format_exc())
            time.sleep(3)

HeartBeatPin = 33
def HeartBeat():
    global PIANO_ON
    global operation_mode
 

    while(True):
        if operation_mode=="manual":
            GPIO.output(HeartBeatPin, True)
            time.sleep(0.5)
            GPIO.output(HeartBeatPin, False)
            time.sleep(1.5)
        elif operation_mode=="auto":
            if PIANO_ON:
                GPIO.output(HeartBeatPin, True)
                time.sleep(0.3)
                GPIO.output(HeartBeatPin, False)
                time.sleep(0.3)
            else:
                GPIO.output(HeartBeatPin, True)
                time.sleep(1.5)
                GPIO.output(HeartBeatPin, False)
                time.sleep(1.5)

def getMySQLWerte():
    DBB = mysql.Database()
    select_query ="SELECT * FROM jetzt"
    global werte
    while(True):
        try:
            #DB = mysql.Database()
            werte = DBB.query(select_query) 
            time.sleep(23)
        except Exception, e:
            DBB = mysql.Database()
            import traceback  
            print traceback.format_exc()          

from datetime import datetime, timedelta
import time

someone_home=True
door_is_open=True
PC_is_running=False
def pinger(): 
    global someone_home
    global PC_is_running
    pc_off_count=0
    last_seen = datetime.now()
    last_seen_home=[datetime.now(),datetime.now(),datetime.now()]
    
    while(True):
        try:
            PC="192.168.1.9"
            ips_to_ping = ["192.168.1.104", "192.168.1.105",PC]
            for no in [0,1,2]:
                ip=ips_to_ping[no]
                time.sleep(15)
                response = os.system("ping -c 1 " + ip)
                if ip==PC:
                    if response == 0:
                        pc_off_count=0
                        PC_is_running=True
                    else:
                        pc_off_count+=1
                        if pc_off_count>=3:
                            pc_off_count=0
                            PC_is_running=False
                else:
                    if response == 0:
                        sp = datetime.now() - last_seen_home[no]
                        print ("%s / %s" % (ip, sp))
                        if sp > timedelta(minutes=120):
                            if int(time.strftime("%H"))>8 and int(time.strftime("%H"))<23:
                                if ip=="192.168.1.104":     #sie ist da
                                    speak("Servus Hasi. Willkommen zu Hause.")
                                elif ip=="192.168.1.105":   #er ist da
                                    speak("Hallo Boss! Willkommen zu Hause.")

                        last_seen_home[no]=datetime.now()
                        last_seen = datetime.now()
                        #print 'someone is here'
                        someone_home=True
                        
            span = datetime.now() - last_seen
            if span > timedelta(minutes=30):
                someone_home=False
            
        except Exception, e:
            import traceback  
            print traceback.format_exc()

wetter_text=""
def get_wetter_text_thread():
    global wetter_text
    while(True):
        try:
            wetter_text= weather.get_weather()
            time.sleep(60*60)   #stunde warten

def speak_weather():
    global wetter_text
    speak(wetter_text)
    
def speak(text):
    call(["mpg123","-q","http://api.voicerss.org/?key=add015f1fdfd41c69a135c7c9b0025df&src=%s&hl=de-de&f=44khz_16bit_mono" % text])
        
firstrun=True
guten_morgen=True
gute_nacht=True
def change_door(channel):
    global door_is_open
    global firstrun
    global gute_nacht
    global guten_morgen
    
    zeit = time.strftime("%H:%M:%S")
    print ("%s guten_morgen:%s gute_nacht:%s firstrun:%s door_is_open:%s" % (zeit, guten_morgen, gute_nacht, firstrun, door_is_open))
        
    if firstrun:
        firstrun=False
        return
    
    if int(time.strftime("%H"))>=5 and int(time.strftime("%H"))<=9 and door_is_open==True and guten_morgen==False:
        guten_morgen=True
        text=("Guten Morgen! Das Wetter für Heute: %s" % weather.get_weather)
        speak(text)
        
    if int(time.strftime("%H"))>=20 and int(time.strftime("%H"))<=23 and door_is_open==False and  gute_nacht==False:
        gute_nacht=True
        speak("Gute Nacht ihr beiden")
           
          
#main loop
#speak_weather()
try:
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(37, GPIO.IN) #Türkontakt ,pull_up_down=GPIO.PUD_DOWN
    GPIO.add_event_detect(37, GPIO.BOTH, callback = change_door, bouncetime = 200)

    GPIO.setup(40, GPIO.OUT)
    GPIO.output(40, True)
    GPIO.setup(38, GPIO.OUT)
    GPIO.output(38, True)
    GPIO.setup(HeartBeatPin, GPIO.OUT)
    GPIO.setup(35, GPIO.OUT)
    GPIO.output(35, True)
    GPIO.setup(36, GPIO.OUT)
    GPIO.output(36, True)
except Exception, e:
    import traceback  
    print traceback.format_exc()

print "warte 15 Sekunden"
time.sleep(15)  #zur sicherheit 
while(True):
    try:
        #init ADC
        ADC_result=[0,0,0,0,0,0,0,0]
        ADC_current_value=[0,0,0,0,0,0,0,0] 
        ADC_conversions=[0,0,0,0,0,0,0,0]
        ADC_conversions_per_minute=[0,0,0,0,0,0,0,0]
        ADC_conversion_Minute=0
        ADC_Channel=1
        i2c_helper = ABEHelpers()
        bus = i2c_helper.get_smbus()
        adc12 = DeltaSigma(bus, 0x68, 0x68, 18)
        adc12.set_pga(1)
        #adc12.set_pga(2)    #max 32C dann in der saettigung des ADC

        #PWM Modul
        rgb = PWM(0x70)	#set address for RGB Led

        #global Variables
        PWM_Werte_ist=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,4095,0]
        PWM_Werte_soll=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,4095,0]
        PIANO_ON=False

        DB = mysql.Database()
        select_query ="SELECT * FROM jetzt"
        werte = DB.query(select_query)  
    
        AussenHelligkeit = 0
        RGBW=[0,0,0,0]
    except Exception, e:
        import traceback  
        print traceback.format_exc()

    try:

        start_new_thread(HeartBeat,())
        start_new_thread(pinger,())
        start_new_thread(adjust_PWM,())
        start_new_thread(RPC_Server,())
        start_new_thread(get_wetter_text_thread,())
        start_new_thread(getMySQLWerte,())

        guten_morgen=False
        gute_nacht=False
        write_to_log("Program started")
        mT = start_new_thread(main_programm(),())
        mT.join()

        write_to_log("fehler in main, neustart")
    except Exception, e: 
        import traceback  
        write_to_log(traceback.format_exc())
        time.sleep(3)


 #region PWM Color
def red():
  rgb.setPWM(0, 4095, 0)
  rgb.setPWM(1, 0, 4095)
  rgb.setPWM(2, 0, 4095)
def green():
  rgb.setPWM(0, 0, 4095)
  rgb.setPWM(1, 4095, 0)
  rgb.setPWM(2, 0, 4095)
def blue():
  rgb.setPWM(0, 0, 4095)
  rgb.setPWM(1, 0, 4095)
  rgb.setPWM(2, 4095, 0)
def magenta():
  rgb.setPWM(0, 4095, 0)
  rgb.setPWM(1, 0, 4095)
  rgb.setPWM(2, 4095, 0)
def cyan():
  rgb.setPWM(0, 0, 4095)
  rgb.setPWM(1, 4095, 0)  	
  rgb.setPWM(2, 4095, 0)
def yellow():
  rgb.setPWM(0, 4095, 0)
  rgb.setPWM(1, 4095, 0)  	
  rgb.setPWM(2, 0, 4095)
def orange():
  rgb.setPWM(1, 4095, 0)
  rgb.setPWM(0, 2048, 2048)  	
  rgb.setPWM(2, 0, 4095)
def random():
  zeit = time.strftime("%H:%M:%S")
  r=random.randint(0, 4095)
  g=random.randint(0, 4095)
  b=random.randint(0, 4095)
  ADC_Result= adc12.read_voltage(1)
  temp = ( ADC_Result - 0.4 )/ 19.5 *1000
  rgb.setPWM(1, 4095, r)
  rgb.setPWM(2, 4095, g)
  rgb.setPWM(3, 4095, b)
  display.gotoLine1()
  display.printtext("R%04dG%04dB%04d" % (r, g, b) )
  display.gotoLine2()
  display.printtext("ADC=%02.3f = %2.3fC" % (ADC_Result, temp) )
#endregion
