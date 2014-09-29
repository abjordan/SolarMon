#!/usr/bin/env python

import MySQLdb

db = MySQLdb.connect(host="localhost",
                     user="solar",
                     passwd="solarpw",
                     db="SolarMon")

cur = db.cursor()

# Time will be in SQL DATETIME format: '1970-01-01 00:00:01'
prod = '''
CREATE TABLE IF NOT EXISTS production
( 
time DATETIME,
current_production_w INTEGER
);'''

cur.execute(prod)

# Insert some fake data
ins = "INSERT INTO production VALUES ('2014-09-29 %02d:00:00', %d);"
for i in range(0, 24):
    s = ins % (i, i)
    cur.execute(s)

db.commit()
db.close()


