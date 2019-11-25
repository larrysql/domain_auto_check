#!/usr/local/bin/python
# -*- coding: utf-8
import sys
sys.path.append("..")
from utils.conn_mysql import conn_mysql,conn_mysql_l
from flask import Flask,url_for,jsonify
from flask import render_template,Blueprint,abort
from flask import request
from jinja2 import TemplateNotFound
import cx_Oracle
import json
reload(sys)
sys.setdefaultencoding('utf-8')

mod = Blueprint('test', __name__,template_folder='templates')

@mod.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)


@mod.route('/chart')
def index():
    value = {'Chrome': 52.9, 'Opera': 1.6, 'Firefox': 27.7}
    return render_template('oracle/ora_load_detail.html',data=value)

@mod.route('/test_ip')
def test_ip():
    #ip = request.headers["X-Real-IP"]
    ip = request.remote_addr
    return jsonify(origin=request.headers.get('X-Forwarded-For', request.remote_addr))
    #return ip

@mod.route('/test_json')
def test_json():
    username,password,host,port,dbname = 'hgame','ora_0046','10.20.1.151','1521','bidb'
    dsn = host + ':' + port + '/' + dbname
    dbora = cx_Oracle.connect(username,password,dsn)
    cursor = dbora.cursor()
    sql = '''select * from 
    				(select u.user_name,pt.BET_AMOUNT 
    				 from 
    				    pt_user_daily_rpt pt left join pt_users u 
    				    on pt.user_id = u.user_id
    				 where  pt.stat_day = trunc(sysdate-1) 
    				    and pt.bet_amount is not null 
    				 order by bet_amount desc
    				 )
			 where rownum<=10
             '''
    cursor.execute(sql)
    rs = cursor.fetchall()
    d = {}
    day,amount,precash = [],[],[]
    for x in rs:
    	day.append(x[0])
    	amount.append(x[1])
    	precash.append(x[2])
    d['day'] = day
    d['amount'] = amount
    d['precash'] = precash
    data = jsonify(d)
    return data
