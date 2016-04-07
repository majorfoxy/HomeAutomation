import os
from datetime import datetime, timedelta
import time
 
someone_home=False
PC_is_running=False
last_seen = datetime.now()
while(True):
    ips_to_ping = ["192.168.1.104", "192.168.1.105"]
    PC="192.168.1.9"
    for ip in ips_to_ping:
        response = os.system("ping -c 1 " + ip)
        if response == 0:
            last_seen = datetime.now()
            #print 'someone is here'
            someone_home=True
            break

    span = datetime.now() - last_seen
    if span > timedelta(minutes=10):
        someone_home=False
    
    response = os.system("ping -c 1 " + PC)
    if response == 0:
        PC_is_running=True
        
    #print someone_home
    time.sleep(3)