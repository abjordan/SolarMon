#!/usr/bin/env python

from flask import Flask, render_template
import MySQLdb
import time

app = Flask(__name__)
db = None

@app.route('/')
def hello_flask():
    return "Hello Flask!"

@app.errorhandler(404)
def page_not_found(error):
    s = "That's a 404. <br/>" + str(error)
    return s, 404


@app.route('/production/today')
def today_prod():
    if db is None:
        abort(404)

    sql_time_fmt = "%Y-%m-%d %H:%M:%S"

    today = time.strftime(sql_time_fmt)
    date = today.split(" ")[0]

    db.ping(True)
    cur = db.cursor()
    cur.execute("SELECT * FROM production WHERE time <= '%s 23:59:59' AND time >= '%s 00:00:00' ORDER BY time;" % (date, date))
    productionData = []
    rows = cur.fetchall()
    for row in rows:
        timestamp = str(row[0]).split(" ")[1]
        prod = row[1]
        productionData.append([timestamp, prod])    
    cur.close()
    db.commit()
    return render_template("production.html", 
                           productionData=productionData,
                           date=date)

@app.route('/chart/test')
def chart_test():
    page = '''
<html>
  <head>
    <Title>Solar Panel Production Today</Title>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      google.setOnLoadCallback(drawChart);
      function drawChart() {
        var data = google.visualization.arrayToDataTable([
          ['Year', 'Sales', 'Expenses'],
          ['2004',  1000,      400],
          ['2005',  1170,      460],
          ['2006',  660,       1120],
          ['2007',  1030,      540]
        ]);

        var options = {
          title: 'Company Performance',
          hAxis: {title: 'Year', titleTextStyle: {color: 'red'}}
        };

        var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));

        chart.draw(data, options);
      }
    </script>
  </head>
  <body>
    <div id="chart_div" style="width: 900px; height: 500px;"></div>
  </body>
</html>
'''
    return page

if __name__=="__main__":
    db = MySQLdb.connect(host="localhost",
                         user="solar",
                         passwd="solarpw",
                         db="SolarMon")
    
    app.debug = True
    app.run(host="0.0.0.0")
