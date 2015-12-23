#!/usr/bin/env python 

import bs4, urllib2, MySQLdb
import time, datetime, json, threading

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

def grab_gross_reading():
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

def grab_microinverter_stats():
    # This is obviously site specific. To get the right URL, open the /inventory page on the enphase web console.
    # Fire up the Chrome Dev Tools (hit F12) and select the "Network" tab. Refresh the page and look in the timeline
    # for a GET to the datatab/inventory_dt.rb call. I chopped off a bunch of URL parameters for things like "make sortable"
    # for each column, etc. but it doesn't seem to matter if you specify which columns you want -- you always get all 8.
    
    site = urllib2.urlopen("http://192.168.1.3/datatab/inventory_dt.rb?locale=en&name=PCU&sEcho=1&iColumns=8&sColumns=part_num%2Cinstalled%2Cserial_num%2Cdevice_status%2Crunning_image%2Cassem_part_num%2Cctrl_part_num%2Clast_rpt_date&iDisplayStart=0&iDisplayLength=25")
    page = site.read()

    # Need to figure out how many microinverters there are. The return from here is a JSON object:
    #   {
    #      'aaData'               : [ [<per inverter info>], ...],
    #      'sEcho'                :  1,
    #      'iTotalRecords'        : <number of inverters available>,
    #      'iTotalDisplayRecords' : <number returned in this query>
    #   }
    # Let's hear it for Hungarian notation!

    j = json.loads(page)
    records = j[u'iTotalRecords']

    # If you have more than 25 microinverters, request all of them
    if len(j[u'aaData']) == records:
        data = j
    else:
        full_site = urllib2.urlopen("http://192.168.1.3/datatab/inventory_dt.rb?locale=en&name=PCU&sEcho=1&iColumns=8&sColumns=part_num%2Cinstalled%2Cserial_num%2Cdevice_status%2Crunning_image%2Cassem_part_num%2Cctrl_part_num%2Clast_rpt_date&iDisplayStart=0&iDisplayLength={0}".format(records))
        full_page = full_site.read()
        data = json.loads(full_page)

    # Data is: [part_number, install_date, serial_num, status, running_image, assembly_part_number, controller_part_no, last_report]
    # We care about serial_num, status, and last_report - the others are less interesting. It's not clear how often they update...
    # Seems to be about every five minutes?
    #
    # We return: [serial_num, status, last_report]
    rows = []
    for inv in data[u'aaData']:
        row = [inv[2], inv[3], inv[7]]
        rows.append(row)

    return rows

def looper():
    global next_call, db, stop

    start_time = time.time()
    while (stop is False):
        results = grab_gross_reading()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print "Got a reading at " + now + " = %f" % results[0]

        ins = "INSERT INTO production VALUES ('%s', %f);" % (now, results[0])
        db.ping(True)
        cur = db.cursor()
        cur.execute(ins)
        cur.close()

        inv_stats = grab_microinverter_stats()
        cur = db.cursor()
        db.ping(True)
        for inv in inv_stats:
            ins = "INSERT INTO inverters VALUES ('{0}', '{1}', '{2}');".format(*inv)
            cur.execute(ins)
        cur.close()

        db.commit()

        sleep_time = 360 - (time.time() - start_time)
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

