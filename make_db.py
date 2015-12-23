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

inverters = '''
CREATE TABLE IF NOT EXISTS inverters 
(
	serial varchar(12), 
	status varchar(255), 
	last_update varchar(32)
);'''

cur.execute(inverters)

db.commit()
db.close()