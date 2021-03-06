#!/usr/local/bin/python
# -*- coding: utf-8
import sys,time
sys.path.append("..")
from utils.conn_mysql import *
from datetime import datetime,timedelta
import socket,struct

def init_data(dh = 1):
    l = []
    now = datetime.now()
    btime = now - timedelta(hours=dh)
    while (btime + timedelta(seconds=10)) < now:
        btime = btime + timedelta(seconds=10)
        ltime = btime.strftime('%Y/%m/%d %H:%M:%S')
        ltime = time.mktime(time.strptime(ltime,'%Y/%m/%d %H:%M:%S'))*1000
        l.append([ltime,0])
    print l
    return l

def get_role_list(user_name):
    db = conn_db()
    cursor = db.cursor()
    sql = ''' SELECT r.role_name FROM 
             role r LEFT JOIN user_role ur
             ON r.id = ur.role_id
             LEFT JOIN users u
             ON ur.user_id = u.id 
             WHERE u.user_name = \'''' + user_name + '''\' '''
    cursor.execute(sql)
    rs_role_name = cursor.fetchall()
    return rs_role_name

def get_user_privs(user_name):
    db = conn_db()
    cursor = db.cursor()
    sql = '''select a.priv_name,listagg(a.priv||'||'||a.priv_func,',') within group(order by a.p_sort_id,a.sort_id),a.p_sort_id
                from(
                    select ppv.priv_name  priv_name 
                        ,pv.priv_name priv,
                        pv.priv_func,
                        pv.sort_id ,
                        ppv.sort_id p_sort_id
                    from 
                        privs pv left join privs ppv
                    on pv.pid = ppv.id
                    where 
                        pv.id in (select priv_id from priv_role 
                                where 
                                    role_id in(select role_id from user_role 
                                            where 
                                                    user_id in(select id from users 
                                                    where 
                                                    user_name = :user_name
                                                            )
                                                )
                                )
                    order by ppv.sort_id,pv.sort_id
                    ) a
                group by a.priv_name,a.p_sort_id
                order by a.p_sort_id'''
    cursor.execute(sql,user_name = user_name)
    rs = cursor.fetchall()
    l_privs = []
    if len(rs)>0:
        for row in rs:
            p_priv_name = row[0]
            l_priv = []
            l1 = row[1].split(',')
            for x in l1:
                l2 = x.split('||')
                l_priv.append(l2)
            l_privs.append([p_priv_name,l_priv]) 
    return l_privs

def rs_to_json(rs,data_type):
    l_data = json.dumps([x[0] for x in rs])
    s_data = json.dumps([{'name':x[0],'value':x[1]} for x in rs])
    if data_type =='data':
        json_data = s_data
    else:
        json_data = l_data
    return json_data

#rs tuple to dict
def makedict(cur):
    cols = [d[0] for d in cur.description]
    def createrow(*args):
        return dict(zip(cols, args))
    return createrow
#ip to number
def ip_to_num(ip='0.0.0.0'):
    ip = ip.strip()
    num = socket.ntohl(struct.unpack("I",socket.inet_aton(str(ip)))[0])
    return num