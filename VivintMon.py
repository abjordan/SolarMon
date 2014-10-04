#!/usr/bin/python 

import bs4, urllib2, MySQLdb
import time, datetime, threading

units = {
    "W": 1,
    "kW": 1000,
    "MW": 1000000,
    "Wh": 1,
    "kWh": 1000,
    "MWh": 1000000 
}

def str_to_watts(s):
    tok = s.strip().split(" ")
    number = float(tok[0])
    unit = tok[1]
    watts = number * units[unit]
    return watts

def grab_reading():
    site = urllib2.urlopen("http://192.168.1.3/production?locale=en")
    page = site.read()

    soup = bs4.BeautifulSoup(page, from_encoding='utf-8')

    current = soup.find('td', text="Currently").find_next('td').string
    today = soup.find('td', text="Today").find_next('td').string
    week = soup.find('td', text="Past Week").find_next('td').string
    auc = soup.find('td', text="Since Installation").find_next('td').string
    
    row = [current, today, week, auc]
    row_w = [str_to_watts(x) for x in row]
    return row_w

def looper():
    global next_call, db, stop

    start_time = time.time()
    while (stop is False):
        results = grab_reading()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print "Got a reading at " + now + " = %f" % results[0]

        ins = "INSERT INTO production VALUES ('%s', %f);" % (now, results[0])
        db.ping(True)
        cur = db.cursor()
        cur.execute(ins)
        cur.close()
        db.commit()

        sleep_time = 600 - (time.time() - start_time)
        print "Sleeping for %f seconds" % sleep_time
        time.sleep( sleep_time )
        start_time = time.time()

if __name__=="__main__":
    db = MySQLdb.connect(host="localhost",
                         user="solar",
                         passwd="solarpw",
                         db="SolarMon")
    
    stop = False
    next_call = time.time()
    looper_thread = threading.Thread(target=looper)
    looper_thread.daemon = True
    looper_thread.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print "Caught interrupt - exiting."
        stop = True

