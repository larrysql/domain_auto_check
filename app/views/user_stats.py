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

mod = Blueprint('user_stats', __name__,template_folder='templates')
#===========================================顶级代理树统计==========================================================
def rs_to_json(rs,data_type):
    l_data = json.dumps([x[0] for x in rs])
    s_data = json.dumps([{'name':x[0],'value':x[1]} for x in rs])
    if data_type =='data':
        json_data = s_data
    else:
        json_data = l_data
    return json_data

@mod.route('/top10_user')
def top10_user():
    return render_template('agent/test_hc.html')

@mod.route('/top10_user_json')
def top10_user_json():
    stat_name = request.args.get('stat_name').strip('\'')
    data_type = request.args.get('type').strip('\'')
    db = conn_db()
    cursor = db.cursor()
    if stat_name == 'top10_bet':
        #投注额top10的用户
        sql = '''select a.* 
                 from (
                       select ut.username,BET_AMOUNT from pt_user_daily_rpt pt,usertree ut
                       where 
                           pt.user_id = ut.userid
                           and stat_day = trunc(sysdate-1)
                           and bet_amount is not null
                           and ut.istester = 0
                           and ut.isdeleted = 0
                       order by bet_amount desc ) a
                 where rownum<=10
                '''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_sale_lottery':
        #销量top10的彩种
        sql = ''' select * from(
                         select stat_content,stat_value 
                         from rt_other_stat_d
                         where 
                            stat_name = 'lottery_amount'
                            and stat_day = trunc(sysdate-1)
                        order by stat_value desc)
                        where rownum<=10
                  '''
        cursor.execute(sql)
        rs = cursor.fetchall() 
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_recharge':
        #充值top10用户
        sql = '''select a.* 
                 from (
                       select ut.username,RECHARGE_AMOUNT from pt_user_daily_rpt pt,usertree ut
                       where 
                           pt.user_id = ut.userid
                           and stat_day = trunc(sysdate-1)
                           and RECHARGE_AMOUNT is not null
                           and ut.istester = 0
                           and ut.isdeleted = 0
                       order by RECHARGE_AMOUNT desc ) a
                 where rownum<=10  
            '''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_user_cnt':
        #用户数最多的代理top10
        sql = '''  
            select * from(
                select root_name,count(*)
                from 
                    (SELECT userid
                            ,parentid,
                            RPAD('.', (level-1)*2, '.') || username AS tree,
                            level dept,
                            CONNECT_BY_ROOT userid AS root_id,
                            CONNECT_BY_ROOT username AS root_name,
                            LTRIM(SYS_CONNECT_BY_PATH(username, '-'), '-') AS lpath,
                            CONNECT_BY_ISLEAF AS leaf
                    FROM   usertree
                    where istester = 0
                        and isdeleted = 0
                        START WITH parentid = 0
                        CONNECT BY parentid = PRIOR userid
                    )
                group by root_name 
                order by 2 desc) 
            where rownum<=10
        '''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_bind_card':
        #绑卡最多的用户
        sql = ''' select * from (select user_name,count(*) from passport.user_bank_info group by user_name order by 2 desc) where rownum<=10 '''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_laxin_user_bet':
        #拉新用户投注额top10
        sql = '''select username,bet_amount 
                from(
                    select ut.username,
                        (select username from usertree where userid = ut.lvtopid) agent,
                        u.registertime,
                        (select nvl(sum(bet_amount),0) from pt_user_daily_rpt p where p.user_id = ut.userid) bet_amount,
                        (select nvl(sum(recharge_amount),0) from pt_user_daily_rpt o where o.user_id = ut.userid) recharge_amount
                    from 
                        usertree ut ,
                        passport.users u 
                    where 
                        ut.userid = u.userid 
                        and u.registertime>=to_date('2017-11-08 09:00:00','yyyy-mm-dd hh24:mi:ss') 
                        and u.registertime<to_date('2017-11-22 00:00:00','yyyy-mm-dd hh24:mi:ss')
                        and ut.istester = 0
                    order by 4 desc
                    )
                where rownum<=10'''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    elif stat_name == 'top10_laxin_user_recharge':
        #拉新用户充值额top10
        sql = '''select username,recharge_amount 
                 from(
                     select ut.username,
                         (select username from usertree where userid = ut.lvtopid) agent,
                         u.registertime,
                         (select nvl(sum(bet_amount),0) from pt_user_daily_rpt p where p.user_id = ut.userid) bet_amount,
                         (select nvl(sum(recharge_amount),0) from pt_user_daily_rpt o where o.user_id = ut.userid) recharge_amount
                     from 
                         usertree ut ,
                         passport.users u 
                     where 
                         ut.userid = u.userid 
                         and u.registertime>=to_date('2017-11-08 09:00:00','yyyy-mm-dd hh24:mi:ss') 
                         and u.registertime<to_date('2017-11-22 00:00:00','yyyy-mm-dd hh24:mi:ss')
                         and ut.istester = 0
                     order by 5 desc
                     )
                 where rownum<=10'''
        cursor.execute(sql)
        rs = cursor.fetchall()  
        json_data = rs_to_json(rs,data_type)
    return json_data
