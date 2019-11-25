#!/usr/local/bin/python
# -*- coding: utf-8
import sys,os
sys.path.append("..")
from utils.conn_mysql import *
from flask import Flask,url_for,jsonify
from flask import render_template,Blueprint,abort
from flask import request,session
from jinja2 import TemplateNotFound
import chartkick
import json
import time,random,datetime
reload(sys)
sys.setdefaultencoding('utf-8')
os.environ["NLS_LANG"] = ".UTF8"

mod = Blueprint('agent', __name__,template_folder='templates')
#===========================================顶级代理树统计==========================================================
count_per_page = 15
@mod.route('/top_agent_tree')
def top_agent_tree():
    # if not session.get('logged_in'):
    #     return render_template('login.html')
    db = conn_db()
    cursor = db.cursor()
    #如果是第一次登录，获取总记录数
    if  not session.get('record_count'):
        sql = '''select count(*)
                     from 
                         (select at.root_name,at.tree,at.dept,
                                 abr.bet_amount,abr.recharge_amount,
                                 u.registertime register_time
                            from MV_RT_AGENT_TREE at
                                left join RT_AGENT_BET_RECHARGE_D abr
                                on at.root_id = abr.root_id
                                and abr.stat_day = to_date('20170901','yyyymmdd')
                                left join passport.users u
                                on at.root_id = u.userid    
                        order by root_name)
                         '''
        cursor.execute(sql)
        record_count = cursor.fetchone()[0]
        session['record_count'] = record_count
        print record_count
    else:
        record_count = session.get('record_count')

    #总页数
    last_count = record_count%count_per_page
    if last_count == 0:
        page_count = record_count/count_per_page
    else: 
        page_count = record_count/count_per_page + 1

    page_no = request.args.get('page_no')
    if page_no is None:
        page_no = 1
    else:
        page_no = int(page_no)

    page_flag = 'top_agent_tree'
    begin_no = (int(page_no) - 1)*count_per_page
    end_no = int(page_no)*count_per_page
    sql = '''select * from
                    (select a.*,rownum rn
                     from 
                         (select at.root_name,at.tree,at.dept,
                                 abr.bet_amount,abr.recharge_amount,
                                 u.registertime register_time
                            from MV_RT_AGENT_TREE at
                                left join RT_AGENT_BET_RECHARGE_D abr
                                on at.root_id = abr.root_id
                                and abr.stat_day = to_date('20170901','yyyymmdd')
                                left join passport.users u
                                on at.root_id = u.userid    
                        order by root_name,at.tree
                        ) a
                    ) 
               where rn>''' + str(begin_no) + ''' and rn <=''' + str(end_no)
    # print sql
    cursor.execute(sql)
    entries = cursor.fetchall()
    s = set(x[0] for x in entries)
    d = {}
    for k in s:
        d[k] = []
        for x in entries:
            if k == x[0]:
                v = [x[1].split('-'),x[2],x[3],x[4],x[5]]
                d[k].append(v)
    entries = sorted(d.iteritems(), key=lambda d:d[0])
    #print d
    cursor.close()
    db.close()
    return render_template('agent/agent_tree.html',**locals())
    #return jsonify(result = l)
#===============================代理树统计=================================================================
@mod.route('/agent_tree')
def agent_tree():
   #获取用户请求的页数和用户名
    page_no = request.args.get('page_no')
    user_name = request.args.get('user_name')
    if page_no is None:
        page_no = 1
    else:
        page_no = int(page_no)
    #创建数据库连接
    db = conn_db()
    cursor = db.cursor()
    #如果是第一次获取查询该用户下面的代理树，获得记录数
    if not session.get(user_name):
        sql = '''select count(*)
                from 
                    (select u.root_name,u.lpath,u.dept,abr.bet_amount,abr.recharge_amount
                    from 
                        (select root_name,lpath,dept,root_id from(
                                SELECT  CONNECT_BY_ROOT username AS root_name,
                                        CONNECT_BY_ROOT userid AS root_id,
                                        LTRIM(SYS_CONNECT_BY_PATH(username, '-'), '-') AS lpath,
                                        level dept,
                                        CONNECT_BY_ISLEAF AS leaf
                                FROM   usertree
                                where istester = 0
                                and isdeleted = 0
                                START WITH username = \'''' + user_name + '''\'
                                CONNECT BY parentid = PRIOR userid
                                ORDER SIBLINGS BY userid
                                ) 
                        where leaf = 1) u
                        left join RT_AGENT_BET_RECHARGE_D abr
                        on u.root_id = abr.root_id
                        and abr.stat_day = trunc(sysdate-1)
                    ) '''
        cursor.execute(sql)
        record_count = cursor.fetchone()[0]
        session[user_name] = record_count
    else:
        record_count = session.get(user_name)

    print u'总记录数',record_count
    #总页数
    last_count = record_count%count_per_page
    if last_count == 0:
        page_count = record_count/count_per_page
    else: 
        page_count = record_count/count_per_page + 1

    page_flag = 'agent_tree'
    begin_no = (int(page_no) - 1)*count_per_page
    end_no = int(page_no)*count_per_page
    sql = '''
            select * from(
                select a.*,rownum rn
                from 
                    (select u.root_name,u.lpath,u.dept,abr.bet_amount,abr.recharge_amount
                    from 
                        (select root_name,lpath,dept,root_id from(
                                SELECT  CONNECT_BY_ROOT username AS root_name,
                                        CONNECT_BY_ROOT userid AS root_id,
                                        LTRIM(SYS_CONNECT_BY_PATH(username, '-'), '-') AS lpath,
                                        level dept,
                                        CONNECT_BY_ISLEAF AS leaf
                                FROM   usertree
                                where istester = 0
                                and isdeleted = 0
                                START WITH username = \'''' + user_name + '''\'
                                CONNECT BY parentid = PRIOR userid
                                ORDER SIBLINGS BY userid
                                ) 
                        where leaf = 1) u
                        left join RT_AGENT_BET_RECHARGE_D abr
                        on u.root_id = abr.root_id
                        and abr.stat_day = trunc(sysdate-1)
                    ) a 
                ) 
            where rn>''' + str(begin_no) + ''' and rn <=''' + str(end_no)
    # print sql
    cursor.execute(sql)
    entries = cursor.fetchall()
    s = set(x[0] for x in entries)
    d = {}
    for k in s:
        d[k] = []
        for x in entries:
            if k == x[0]:
                v = [x[1].split('-'),x[2],x[3],x[4],x[5]]
                d[k].append(v)
    entries = sorted(d.iteritems(), key=lambda d:d[0])
    #print d
    cursor.close()
    db.close()
    return render_template('agent/agent_tree.html',**locals())
#===============================拉新活动用户统计=================================================================
@mod.route('/activity')
def activity():
    db = conn_db()
    cursor = db.cursor()
    sql = '''select ut.username,
                 (select username from usertree where userid = ut.lvtopid) as agent,
                 (select nvl(sum(bet_amount),0) from pt_user_daily_rpt p where p.user_id = ut.userid) bet,
                 (select nvl(sum(recharge_amount),0) from pt_user_daily_rpt o where o.user_id = ut.userid) recharge,
                  u.registertime
             from 
                 usertree ut ,
                 passport.users u 
             where 
                 ut.userid = u.userid 
                 and u.registertime>=to_date('2017-11-08 09:00:00','yyyy-mm-dd hh24:mi:ss') 
                 and u.registertime<to_date('2017-11-22 00:00:00','yyyy-mm-dd hh24:mi:ss')
                 and ut.istester = 0
             order by 2 '''
    cursor.execute(sql)
    entries = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('agent/activity_user.html',**locals())
    