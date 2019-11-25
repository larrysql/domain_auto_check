#!/usr/local/bin/python
# -*- coding: utf-8
__author__ = 'liangshiqiang'
import os, sys, string
import MySQLdb
import MySQLdb.cursors
import cx_Oracle

# 连接数据库　
def conn_mysql():
    try:
        conn = MySQLdb.connect(host='172.16.110.165',user='powerm',passwd='powerm',db='powerm',port=3310,cursorclass = MySQLdb.cursors.DictCursor)
        conn.set_character_set('utf8')
        return conn
    except Exception, e:
        print e
        sys.exit()

def conn_mysql_l():
    try:
        conn = MySQLdb.connect(host='172.16.110.165',user='powerm',passwd='powerm',db='powerm',port=3310)
        conn.set_character_set('utf8')
        return conn
    except Exception, e:
        print e
        sys.exit()

def conn_ora(inst_id):
    try:
        dbmysql = conn_mysql()
        cursor = dbmysql.cursor()
        cursor.execute("select ip_addr,port,inst_name,db_name,dba,password from ora_inst where id = %s" %(inst_id))
        rs = cursor.fetchone()
        username,password = rs['dba'],rs['password']
        dsn = rs['ip_addr'] + ':' + str(rs['port']) + '/' + rs['db_name']
        dbora = cx_Oracle.connect(username,password,dsn)
        return dbora
    except Exception,e:
        print '!!!!!!!!!!!!!!!!11',e
def conn_db(username='hgame',password='ora_0046',host='10.20.1.151',port=1521,db_name='bidb'):
     dsn = host + ':' + str(port) + '/' + db_name
     db = cx_Oracle.connect(username,password,dsn)
     return db

def rows_to_dict_list(cursor):
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]





















