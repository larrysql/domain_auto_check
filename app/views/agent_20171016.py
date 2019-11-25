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
@mod.route('/top_agent_tree')
def top_agent_tree():
    page_no = request.args.get('page_no')
    print page_no
    if page_no is None:
        page_no = 1
    else:
        page_no = int(page_no)
    page_flag = 'top_agent_tree'

    db = conn_db()
    cursor = db.cursor()
    begin_no = (int(page_no) - 1)*20
    end_no = int(page_no)*20
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
                        order by root_name
                        ) a
                    ) '''
              where rn>''' + str(begin_no) + ''' and rn <=''' + str(end_no)
    # print sql
    cursor.execute(sql)
    entries = cursor.fetchall()
    if len(entries) == 20:
        end_flag = 0
    else:
        end_flag = 1
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
    page_no = request.args.get('page_no')
    user_name = request.args.get('user_name')
    print page_no
    if page_no is None:
        page_no = 1
    else:
        page_no = int(page_no)
    page_flag = 'agent_tree'
    db = conn_db()
    cursor = db.cursor()
    begin_no = (int(page_no) - 1)*20
    end_no = int(page_no)*20
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
                        and abr.stat_day = to_date('20170901','yyyymmdd')
                    ) a 
                ) 
            where rn>''' + str(begin_no) + ''' and rn <=''' + str(end_no)
    # print sql
    cursor.execute(sql)
    entries = cursor.fetchall()
    print entries
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