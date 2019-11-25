#!/usr/local/bin/python
# -*- coding: utf-8
import sys,os
sys.path.append("..")
from utils.conn_mysql import *
from utils.tools import *
from flask import Flask,url_for,jsonify,redirect
from flask import render_template,Blueprint,abort
from flask import request,session
from jinja2 import TemplateNotFound
import chartkick
import json
import time,random,datetime
import hashlib
from flask.GD import gs_tool,client
reload(sys)
sys.setdefaultencoding('utf-8')
os.environ["NLS_LANG"] = ".UTF8"

mod = Blueprint('domain', __name__,template_folder='templates')
#===========================================顶级代理树统计==========================================================
def rs_to_json(rs,data_type=None):
    l_data = json.dumps([x[0] for x in rs])
    s_data = json.dumps([{'name':x[0],'value':x[1]} for x in rs])
    # s_data = json.dumps([x[1] for x in rs])
    if data_type =='data':
        json_data = s_data
    else:
        json_data = l_data
    return json_data
count_per_page = 12
@mod.route('/domain_query', methods = ['GET', 'POST'])
def domain_query(signal=None):
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        rs_role_name = get_role_list(username)
        l_role_name = [x[0] for x in rs_role_name]
        if 'admin' in l_role_name or 'domain_admin' in l_role_name:
            domain_admin_flag = 'Y'
        else:
            domain_admin_flag = 'N'
        if request.method == 'GET':
            domain_name = request.args.get('domain_name')
            user_name = request.args.get('user_name')
            status = request.args.get('status')
            domain_class = request.args.get('domain_class')
            signal = request.args.get('signal')
            if domain_name is None:domain_name = ''
            if user_name is None:user_name = ''
            if status is None:status = ''
            if domain_class is None:domain_class = ''
        elif request.method == 'POST':
            # column_name,column_value = request.form.get('column_name'),request.form.get('column_value')
            domain_name = request.form.get('domain_name')
            user_name = request.form.get('user_name')
            status = request.form.get('status')
            domain_class = request.form.get('domain_class')
            method = 'POST'
        sql = '''select d.id,d.domain_name,d.account_name,d.email,d.phone,d.postal_code,d.expire_date,
                           (case when u.user_name is null then '--' else u.user_name end) as user_name,
                           (case when status=0  then '可用' else '不可用' end) as status,
                           d.url,
                            (case d.is_add_firewall when 0 then '是' else '否' end) is_add_firewall,
                             d.domain_class
                           from domain d left join users u
                           on d.user_id = u.id
                     where 1 = 1 '''
        #print 'domain_name === ',domain_name
        if domain_name != '':
            sql = sql + '''and domain_name like \'%''' + domain_name + '''%\' ''' 
        if user_name != '':
            sql = sql + '''and user_name like \'%''' + user_name + '''%\' ''' 
        if status != '':
            sql = sql + '''and status = ''' + status + ''' '''
        if domain_class != '':
            sql = sql + '''and domain_class = \'''' + domain_class + '''\' ''' 
        if domain_admin_flag == 'Y':
            sql = sql + '''order by d.id'''
        else:
            sql = sql + '''and user_name = \'''' + username + '''\'order by d.id'''
        #print 'sql======',sql
        #print 'domain_admin_flag====',domain_admin_flag
        cursor.execute(sql)
        rs = cursor.fetchall()
        # #处理分页
        # #获取页数
        # record_count = len(rs)
        # last_count = record_count%count_per_page
        # if last_count == 0:
        #     page_count = record_count/count_per_page
        # else: 
        #     page_count = record_count/count_per_page + 1
        # #获取开始记录和结束记录序号
        # page_no = request.args.get('page_no')
        # if page_no is None:
        #     page_no = 1
        # else:
        #     page_no = int(page_no)
        # begin_no = (int(page_no) - 1)*count_per_page
        # end_no = int(page_no)*count_per_page
        # #返回结果集
        # rs = rs[begin_no:end_no]
        # print page_no,begin_no,end_no,page_count
        return render_template('domain/domain_query.html',**locals())
    else:
        return render_template('login.html')

@mod.route('/add_domain', methods = ['GET', 'POST'])
def add_domain():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        if request.method == 'GET':
            return render_template('domain/input_domain_info.html')
        elif request.method == 'POST':
            group_id = request.form.get('group_id')
            user_group_id = request.form.get('user_group_id')
            account_name = request.form.get('account_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            expire_date = request.form.get('expire_date')
            postal_code = int(request.form.get('postal_code'))
            user_name = request.form.get('user_name')
            status = request.form.get('status')
            url = request.form.get('url')
            is_add_firewall = request.form.get('is_add_firewall')
            domain_class = request.form.get('domain_class')
            # #获取用户ID
            print 'user_name ====',user_name
            if user_name is not None:
                cursor.execute('select id from users u where u.user_name = :user_name',user_name=user_name)
                user_id = cursor.fetchone()[0]
            else:
                user_id = None
            #处理状态
            if status == '可用':
                status = 0
            else:
                status = 1
            #处理防火墙状态
            if is_add_firewall == '是':
                is_add_firewall = 0
            else:
                is_add_firewall = 1
            domain_names = request.form.get('domain_name')
            for domain_name in set(domain_names.strip().split()):
                sql = 'select seq_domain.nextval from dual'
                cursor.execute(sql)
                domain_id = cursor.fetchone()[0]
                sql = 'select seq_domain_group_domain.nextval from dual'
                cursor.execute(sql)
                domain_group_domain_id  = cursor.fetchone()[0]
                #print str(domain_id),domain_name,account_name,email,phone,expire_date,postal_code,user_name,status,url,is_add_firewall,domain_class,user_id
                #插入到数据库中
                sql = '''insert into domain(id,account_name,domain_name,email,phone,postal_code,expire_date,status,url,
                     is_add_firewall,domain_class,user_id,domain_group_id) 
                     values(:domain_id,:account_name,:domain_name,:email,:phone,:postal_code,to_date(:expire_date,'mm/dd/yyyy'),:status,:url,:is_add_firewall,
                     :domain_class,:user_id,:group_id) '''
                cursor.execute(sql,domain_id=domain_id,account_name=account_name,domain_name=domain_name,email=email,phone=phone,postal_code=postal_code,expire_date=expire_date,\
                            status=status,url=url,is_add_firewall=is_add_firewall,domain_class=domain_class,user_id=user_id,group_id=group_id)
                sql = '''insert into domain_group_domain(id,group_id,domain_id) values(:domain_group_domain_id,:user_group_id,:domain_id)'''
                cursor.execute(sql,domain_group_domain_id=domain_group_domain_id,user_group_id=user_group_id,domain_id=domain_id)
                db.commit()
                #db.close()
            return redirect('/domain_query?signal=add_domain')
    else:
        return render_template('login.html')


@mod.route('/update_domain', methods = ['GET', 'POST'])
def update_domain():
    if session.get('logged_in'):
        if request.method == 'GET':
            domain_id = request.args.get('domain_id')
            db = conn_db()
            cursor = db.cursor()
            sql = ''' select d.id,d.domain_name,d.account_name,d.email,d.phone,
                             to_char(d.expire_date,'mm/dd/yyyy'),
                             d.postal_code,
                             (case when u.user_name is null  then '无' else u.user_name end) as user_name,
                             (case when d.status=0  then '可用' else '不可用' end) as status,
                             d.url,(case d.is_add_firewall when 0 then '是' else '否' end) is_add_firewall,
                             d.domain_class
                       from domain d left join users u 
                       on d.user_id = u.id 
                       where d.id = ''' + domain_id
            cursor.execute(sql)
            rs = cursor.fetchone()
            sql = 'select user_name from users where is_hgame_user = 1  order by user_name'
            cursor.execute(sql) 
            rs_users = cursor.fetchall()
            #sql = ' '
            #db.close()
            return render_template('domain/update_domain_info.html',**locals())
        #执行update
        elif request.method == 'POST':
            domain_id = request.form.get('domain_id')
            domain_name = request.form.get('domain_name')
            account_name = request.form.get('account_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            expire_date = request.form.get('expire_date')
            postal_code = int(request.form.get('postal_code'))
            user_name = request.form.get('user_name')
            status = request.form.get('status')
            url = request.form.get('url')
            is_add_firewall = request.form.get('is_add_firewall')
            domain_class = request.form.get('domain_class')
            #建立数据库链接
            db = conn_db()
            cursor = db.cursor()
            #print 'user_name=====',user_name,domain_name,status
            if user_name != None:
                # #获取用户ID
                cursor.execute('select id from users u where u.user_name = :user_name',user_name=user_name)
                user_id = cursor.fetchone()[0]
            else:
                user_id = None
            #处理状态
            if status == '可用':
                status = 0
            else:
                status = 1
            #处理防火墙状态
            if is_add_firewall == '是':
                is_add_firewall = 0
            else:
                is_add_firewall = 1
            # user_id = 3
            sql = '''update domain set domain_name = :domain_name,account_name = :account_name,email = :email,phone=:phone,
                    expire_date=to_date(:expire_date,'mm/dd/yyyy'),postal_code=:postal_code,
                    user_id = :user_id,status = :status,url = :url,is_add_firewall = :is_add_firewall,
                    domain_class = :domain_class where id = :domain_id
                 '''
            cursor.execute(sql,domain_name=domain_name,account_name=account_name,email=email,phone=phone,expire_date=expire_date,postal_code=postal_code,\
                            user_id=user_id,status=status,url=url,is_add_firewall=is_add_firewall,domain_class=domain_class,domain_id=domain_id)
            db.commit()
            #db.close()
            return redirect('/domain_query?signal=update_domain')
    else:
        return render_template('login.html')

@mod.route('/delete_domain')
def delete_domain():
    if session.get('logged_in'):
        if request.method == 'GET':
            domain_id = int(request.args.get('domain_id'))
            db = conn_db()
            cursor = db.cursor()
            sql = 'delete from domain where id = :domain_id'
            cursor.execute(sql,domain_id=domain_id)
            db.commit()
            #db.close()
            return redirect('/domain_query?signal=delete_domain')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@mod.route('/disable_domain')
def disable_domain():
    if session.get('logged_in'):
        if request.method == 'GET':
            domain_id = int(request.args.get('domain_id'))
            status = int(request.args.get('status'))
            if status == 1:
                status,signal = 0,'enable_domain'
            else:
                status,signal = 1,'disable_domain'
            db = conn_db()
            cursor = db.cursor()
            sql = 'update domain set  status = :status where id = :domain_id'
            cursor.execute(sql,domain_id=domain_id,status=status)
            db.commit()
            #db.close()
            return redirect('/domain_query?signal='+signal)
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

def get_domain_mon(group_id, username):
    db = conn_db()
    cur = db.cursor()
    if int(group_id)<5:
        domain_mon_log = 'domain_mon_log'
        domain_open_pct = 'domain_open_pct'
    elif int(group_id) in [5,6]:
        domain_mon_log = 'domain_mon_log_2hz'
        domain_open_pct = 'domain_open_pct_2hz'
    else:
        domain_mon_log = 'domain_mon_log_lgv'
        domain_open_pct = 'domain_open_pct_lgv'

    sql = ''' select * from(
                             select dl.loc_name,d.domain_name,dop.open_pct*100 open_pct,dml.time_namelookup,dml.time_total,http_code
                             from
                                domain_location dl
                                left join
                                (select location_id,domain_id,time_namelookup,time_total,http_code
                                 from {0} where mon_id = (select max(mon_id) from {1}) 
                                       and (http_code = '200' or http_code = '302')
                                 ) dml 
                            on dl.id = dml.location_id
                                 left join
                                (select domain_id,open_pct 
                                 from {1}
                                 where mon_id = (select max(mon_id) from {1})
                                 ) dop
                            on dml.domain_id = dop.domain_id
                                left join domain d
                            on dop.domain_id = d.id
                             where d.id in(select domain_id from domain_group_domain 
                                            where 
                                                group_id in
                                                (select group_id from domain_group_user dgu 
                                                 where 
                                                      dgu.user_id = (select id from users where user_name = '{2}')
                                                )
                                        ) and d.domain_group_id = '{3}'
                            )
                '''.format(domain_mon_log, domain_open_pct, username, group_id)
    sql1 = sql + 'where open_pct>60  order by loc_name,time_total'
    cur.execute(sql1)
    rs1 = cur.fetchall()
    sql2 = sql + ' where open_pct<60  order by loc_name,time_total'
    cur.execute(sql2)
    rs2 = cur.fetchall()
    sql = ''' select * from(
                             select dl.loc_name,d.domain_name,dop.open_pct*100 open_pct,dml.time_namelookup,dml.time_total,http_code
                             from
                                domain_location dl
                                left join
                                (select location_id,domain_id,time_namelookup,time_total,http_code
                                 from {0} where mon_id = (select max(mon_id) from {1}) 
                                       and http_code <> '200' and http_code <> '302'
                                 ) dml 
                            on dl.id = dml.location_id
                                 left join
                                (select domain_id,open_pct 
                                 from {1}
                                 where mon_id = (select max(mon_id) from {1})
                                 ) dop
                            on dml.domain_id = dop.domain_id
                                left join domain d
                            on dop.domain_id = d.id
                             where d.id in(select domain_id from domain_group_domain 
                                            where 
                                                group_id in
                                                (select group_id from domain_group_user dgu 
                                                 where 
                                                      dgu.user_id = (select id from users where user_name = '{2}')
                                                )
                                        ) and d.domain_group_id = '{3}'
                            )  order by loc_name,time_total
                '''.format(domain_mon_log, domain_open_pct, username, group_id)
    cur.execute(sql)
    rs3 = cur.fetchall()
    return [rs1,rs2,rs3]

@mod.route('/domain_mon', methods = ['GET', 'POST'])
def domain_mon():
    if session.get('logged_in'):
        username = session['username']
        submit = request.form.get('submit')
        print(submit)
        db = conn_db()
        cur = db.cursor()
        group = request.form.get('search')
        rs1 = get_domain_mon('1', username)
        rs2 = get_domain_mon('4',username)
        rs3 = get_domain_mon('3',username)
        rs5 = get_domain_mon('5',username)
        rs6 = get_domain_mon('6',username)
        def rs_li(rs):
            rs[0].sort(lambda x, y: cmp(x[4], y[4]))
            rs[1].sort(lambda x, y: cmp(x[4], y[4]))
            rs[2].sort(lambda x, y: cmp(x[4], y[4]))
            return rs[0] + rs[1] + rs[2]
        if submit== '二号站':
            rs = rs_li(rs5)
        elif submit=='一号站':
            rs = rs_li(rs1)
        elif submit=='其它':
            rs = rs_li(rs2)
        elif submit=='一号站移动端':
            rs = rs_li(rs3) 
        elif submit=='二号站移动端':
            rs = rs_li(rs6)
        elif submit=='LGV':
            rs = rs_li(rs7)
        else:
            rs01 = rs1[0] + rs2[0] + rs3[0] + rs6[0] + rs5[0]
            rs01.sort(lambda x, y: cmp(x[4], y[4]))
            rs02 = rs1[1] + rs2[1] + rs3[1] + rs6[1] + rs5[1]
            rs02.sort(lambda x, y: cmp(x[4], y[4]))
            rs03 = rs1[2] + rs2[2] + rs3[2] + rs6[2] + rs5[2]
            rs03.sort(lambda x, y: cmp(x[4], y[4]))
            rs = rs01 + rs02 + rs03
        l = [x[0] for x in rs]
        # l_loc = list(set(l)).sort(key=l.index)
        l_loc = list(set(l))
        l_all = []
        for loc in l_loc:
            l_tmp = [loc]
            l_info = [[x[1],x[2],x[3],x[4],x[5]] for x in rs if x[0]==loc]
            l_tmp.append(l_info)
            l_all.append(l_tmp)
        return render_template('domain/mon_domain.html',**locals())
    else:
        return render_template('login.html')

@mod.route('/domain_push')
def domain_push():
    if request.method == 'GET':
        ip = request.args.get('ip')
        request_type = request.args.get('type')
        db = conn_db()
        cur = db.cursor()
        #判断请求类型
        if request_type == 'm':
            tab_name = 'domain_push_m'
            push_type = 'm'
        else:
            tab_name = 'domain_push'
            push_type = 'p'
        #获取该ip所属大区
        num = ip_to_num(ip)
        sql = '''select loc_id,loc_name from domain_ip_location dil 
                 where 
                         :num between begin_ip_num and end_ip_num
                         and loc_id in(select id from domain_province)
                ''' 
        cur.execute(sql,num=num)
        rs1 = cur.fetchone()
        if rs1:
            #print 'ip=====',rs1[0],rs1[1].encode('gbk')
            print 'ip=====',ip,rs1[0],rs1[1]
            prov_id = rs1[0]
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = (select big_loc_id from domain_big_prov_map where prov_id = :prov_id)
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql,prov_id=prov_id)
        else:
            print 'ip=====',ip
            prov_id = ''
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = 0
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql)
        #cur.rowfactory = makedict(cur)
        rs =cur.fetchall()
        #
        if len(rs) < 6:
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = 0
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql)
            rs =cur.fetchall()
        l = [x[:2] for x in rs]
        j = json.dumps(l)
        #开始将信息插入到访问记录表domain_push_log中
        ip_loc_id = prov_id
        ip_big_loc_id,push_stat_id = rs[0][2],rs[0][3]
        try:
            sql = '''insert into domain_push_log(id,ip,num_ip,ip_loc_id,ip_big_loc_id,push_type,push_stat_id) 
                     values(seq_domain_push_log.nextval,:ip,:num_ip,:ip_loc_id,:ip_big_loc_id,:push_type,:push_stat_id)
                   '''
            cur.execute(sql,ip=ip,num_ip=num,ip_loc_id=ip_loc_id,ip_big_loc_id=ip_big_loc_id,push_type=push_type,push_stat_id=push_stat_id)
            db.commit()
            cur.close()
            db.close()
        except Exception,e:
            print '将信息插入到访问记录表domain_push_log中失败' + str(e)
            cur.close()
            db.close()
        #print type(j)
        return j
@mod.route('/domain_push_2hz')
def domain_push_2hz():
    if request.method == 'GET':
        ip = request.args.get('ip')
        request_type = request.args.get('type')
        db = conn_db()
        cur = db.cursor()
        #判断请求类型
        if request_type == 'm':
            tab_name = 'domain_push_m_2hz'
            push_type = 'm'
        else:
            tab_name = 'domain_push_2hz'
            push_type = 'p'
        #获取该ip所属大区
        num = ip_to_num(ip)
        sql = '''select loc_id,loc_name from domain_ip_location dil 
                 where 
                         :num between begin_ip_num and end_ip_num
                         and loc_id in(select id from domain_province)
                ''' 
        cur.execute(sql,num=num)
        rs1 = cur.fetchone()
        if rs1:
            #print 'ip=====',rs1[0],rs1[1].encode('gbk')
            print 'ip=====',ip,rs1[0],rs1[1]
            prov_id = rs1[0]
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = (select big_loc_id from domain_big_prov_map where prov_id = :prov_id)
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql,prov_id=prov_id)
        else:
            print 'ip=====',ip
            prov_id = ''
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = 0
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql)
        #cur.rowfactory = makedict(cur)
        rs =cur.fetchall()
        #
        if len(rs) < 4:
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                         from 
                             domain d ,%s dp 
                         where 
                              d.id = dp.DOMAIN_ID 
                              and dp.BIG_LOC_ID = 0
                              and dp.stat_id = (select max(stat_id) from %s)
                        ''' % (tab_name, tab_name)
            cur.execute(sql)
            rs = cur.fetchall()
        l = [x[:2] for x in rs]
        j = json.dumps(l)
        try:
            #开始将信息插入到访问记录表domain_push_log中
            ip_loc_id = prov_id
            ip_big_loc_id,push_stat_id = rs[0][2],rs[0][3]
            sql = '''insert into domain_push_log_2hz(id,ip,num_ip,ip_loc_id,ip_big_loc_id,push_type,push_stat_id) 
                     values(seq_domain_push_log_2hz.nextval,:ip,:num_ip,:ip_loc_id,:ip_big_loc_id,:push_type,:push_stat_id)
                   '''
            cur.execute(sql,ip=ip,num_ip=num,ip_loc_id=ip_loc_id,ip_big_loc_id=ip_big_loc_id,push_type=push_type,push_stat_id=push_stat_id)
            db.commit()
            cur.close()
            db.close()
        except Exception,e:
            print '将信息插入到访问记录表domain_push_log_2hz中失败' + str(e)
            cur.close()
            db.close()
        #print type(j)
        return j
@mod.route('/domain_push_lgv')
def domain_push_lgv():
    if request.method == 'GET':
        ip = request.args.get('ip')
        db = conn_db()
        cur = db.cursor()
        tab_name = 'domain_push_lgv'
        #获取该ip所属大区
        num = ip_to_num(ip)
        sql = '''select loc_id,loc_name from domain_ip_location dil 
                 where 
                         :num between begin_ip_num and end_ip_num
                         and loc_id in(select id from domain_province)
                '''
        cur.execute(sql,num=num)
        rs1 = cur.fetchone()
        if rs1:
            #print 'ip=====',rs1[0],rs1[1].encode('gbk')
            print 'ip=====',ip,rs1[0],rs1[1]
            prov_id = rs1[0]
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = (select big_loc_id from domain_big_prov_map where prov_id = :prov_id)
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql,prov_id=prov_id)
        else:
            print 'ip=====',ip
            prov_id = ''
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                 from 
                     domain d ,%s dp 
                 where 
                      d.id = dp.DOMAIN_ID 
                      and dp.BIG_LOC_ID = 0
                      and dp.stat_id = (select max(stat_id) from %s)
                '''%(tab_name,tab_name)
            cur.execute(sql)
        #cur.rowfactory = makedict(cur)
        rs =cur.fetchall()
        #
        if len(rs) < 4:
            sql = '''select d.domain_name,dp.rank_num rank,dp.BIG_LOC_ID,dp.stat_id
                         from 
                             domain d ,%s dp 
                         where 
                              d.id = dp.DOMAIN_ID 
                              and dp.BIG_LOC_ID = 0
                              and dp.stat_id = (select max(stat_id) from %s)
                        ''' % (tab_name, tab_name)
            cur.execute(sql)
            rs = cur.fetchall()
        l = [x[:2] for x in rs]
        j = json.dumps(l)
        try:
            #开始将信息插入到访问记录表domain_push_log中
            ip_loc_id = prov_id
            ip_big_loc_id,push_stat_id = rs[0][2],rs[0][3]
            sql = '''insert into domain_push_log_lgv(id,ip,num_ip,ip_loc_id,ip_big_loc_id,push_stat_id) 
                     values(seq_domain_push_log_lgv.nextval,:ip,:num_ip,:ip_loc_id,:ip_big_loc_id,:push_stat_id)
                   '''
            cur.execute(sql,ip=ip,num_ip=num,ip_loc_id=ip_loc_id,ip_big_loc_id=ip_big_loc_id,push_stat_id=push_stat_id)
            db.commit()
            cur.close()
            db.close()
        except Exception,e:
            print '将信息插入到访问记录表domain_push_log_2hz中失败' + str(e)
            cur.close()
            db.close()
        #print type(j)
        return j

#域名推送统计
@mod.route('/domain_push_stat',methods = ['GET', 'POST'])
def domain_push_stat():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        d_date = {'h':'sysdate-1/24','d':'sysdate-1','w':'sysdate-7','m':'add_months(sysdate,-1)','3m':'add_months(sysdate,-3)',}
        d_pt = {'p':['PC端','v_domain_push_log'],'m':['移动端','v_domain_push_log_m']}
        d_range = {'h':'最近1小时','d':'最近1天','w':'最近1周','m':'最近1个月','3m':'最近3个月'}
        stat_type = 'domain'
        if request.method == 'GET':
            push_type = request.args.get('push_type','p')
            sort_order = request.args.get('sort_order')
            period = request.args.get('period')
            #判断推送类型，pc端或移动端
            str_push_type, view_name = d_pt[push_type][0], d_pt[push_type][1]
            #判断查询周期，小时，天，星期，月，3个月
            str_date = d_date.get(period)
            query_range = d_range.get(period,'最近1天')
            if str_date is None:return render_template('login.html')
            str_sql = ' and write_time >= %s'%(str_date)
        elif request.method == 'POST':
            push_type = request.form.get('push_type')
            period = request.form.get('period')
            begin_date,end_date = request.form.get('begin_date'),request.form.get('end_date')
            str_push_type, view_name = d_pt[push_type][0], d_pt[push_type][1]
            #print begin_date,end_date
            str_sql = ''' and write_time >= to_date('%s','yyyy-mm-dd hh24:mi:ss') 
                          and  write_time <= to_date('%s','yyyy-mm-dd hh24:mi:ss')
                       ''' % (begin_date,end_date)
            query_range = begin_date.strip()[:10] + '到' + end_date.strip()[:10]
            query_range = query_range.replace('-','')
        #开始执行查询
        sql = '''select rownum,a.*
                from (
                    select domain_name,count(*) cnt , '%s' as push_type
                     from 
                         %s 
                     where 
                         push_type = '%s'%s
                     group by domain_name 
                     order by 2 desc
                 ) a
               ''' % (str_push_type,view_name,push_type,str_sql)
        #print sql
        cursor.execute(sql)
        rs = cursor.fetchall()
        if len(rs)>=10:
            l = [[rs[i][1],rs[i][2]] for i in range(10)]
        else:
            l = [[x[1],x[2]] for x in rs]
        l_data = rs_to_json(l,)
        s_data = rs_to_json(l,'data')
        print l_data
        print s_data
    return render_template('domain/domain_push_stat.html',**locals())

#博猫域名推送统计
@mod.route('/domain_push_stat_lgv',methods = ['GET', 'POST'])
def domain_push_stat_lgv():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        d_date = {'h':'sysdate-1/24','d':'sysdate-1','w':'sysdate-7','m':'add_months(sysdate,-1)','3m':'add_months(sysdate,-3)',}
        d_pt = {'p':['PC端','v_domain_push_log_lgv'],'m':['移动端','v_domain_push_log_m_lgv']}
        d_range = {'h':'最近1小时','d':'最近1天','w':'最近1周','m':'最近1个月','3m':'最近3个月'}
        stat_type = 'domain'
        if request.method == 'GET':
            push_type = request.args.get('push_type','p')
            sort_order = request.args.get('sort_order')
            period = request.args.get('period')
            #判断推送类型，pc端或移动端
            str_push_type,view_name = d_pt[push_type][0],d_pt[push_type][1]
            #判断查询周期，小时，天，星期，月，3个月
            str_date = d_date.get(period)
            query_range = d_range.get(period,'最近1天')
            if str_date is None:return render_template('login.html')
            str_sql = ' and write_time >= %s'%(str_date)
        elif request.method == 'POST':
            push_type = request.form.get('push_type')
            period = request.form.get('period')
            begin_date,end_date = request.form.get('begin_date'),request.form.get('end_date')
            str_push_type, view_name = d_pt[push_type][0], d_pt[push_type][1]
            #print begin_date,end_date
            str_sql = ''' and write_time >= to_date('%s','yyyy-mm-dd hh24:mi:ss') 
                          and  write_time <= to_date('%s','yyyy-mm-dd hh24:mi:ss')
                       ''' % (begin_date,end_date)
            query_range = begin_date.strip()[:10] + '到' + end_date.strip()[:10]
            query_range = query_range.replace('-','')
        #开始执行查询
        sql = '''select rownum,a.*
                from (
                    select domain_name,count(*) cnt , '%s' as push_type
                     from 
                         %s 
                     where 
                         push_type = '%s'%s
                     group by domain_name 
                     order by 2 desc
                 ) a
               ''' % (str_push_type,view_name,push_type,str_sql)
        #print sql
        cursor.execute(sql)
        rs = cursor.fetchall()
        if len(rs)>=10:
            l = [[rs[i][1],rs[i][2]] for i in range(10)]
        else:
            l = [[x[1],x[2]] for x in rs]
        l_data = rs_to_json(l,)
        s_data = rs_to_json(l,'data')
        print l_data
        print s_data
    return render_template('domain/domain_push_stat_lgv.html',**locals())

#2HZ域名推送统计
@mod.route('/domain_push_stat_2hz',methods = ['GET', 'POST'])
def domain_push_stat_2hz():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        d_date = {'h':'sysdate-1/24','d':'sysdate-1','w':'sysdate-7','m':'add_months(sysdate,-1)','3m':'add_months(sysdate,-3)',}
        d_pt = {'p':['PC端','v_domain_push_log_2hz'],'m':['移动端','v_domain_push_log_m_2hz']}
        d_range = {'h':'最近1小时','d':'最近1天','w':'最近1周','m':'最近1个月','3m':'最近3个月'}
        stat_type = 'domain'
        if request.method == 'GET':
            push_type = request.args.get('push_type','p')
            sort_order = request.args.get('sort_order')
            period = request.args.get('period')
            #判断推送类型，pc端或移动端
            str_push_type,view_name = d_pt[push_type][0],d_pt[push_type][1]
            #判断查询周期，小时，天，星期，月，3个月
            str_date = d_date.get(period)
            query_range = d_range.get(period,'最近1天')
            if str_date is None:return render_template('login.html')
            str_sql = ' and write_time >= %s'%(str_date)
        elif request.method == 'POST':
            push_type = request.form.get('push_type')
            period = request.form.get('period')
            begin_date,end_date = request.form.get('begin_date'),request.form.get('end_date')
            str_push_type, view_name = d_pt[push_type][0], d_pt[push_type][1]
            #print begin_date,end_date
            str_sql = ''' and write_time >= to_date('%s','yyyy-mm-dd hh24:mi:ss') 
                          and  write_time <= to_date('%s','yyyy-mm-dd hh24:mi:ss')
                       ''' % (begin_date,end_date)
            query_range = begin_date.strip()[:10] + '到' + end_date.strip()[:10]
            query_range = query_range.replace('-','')
        #开始执行查询
        sql = '''select rownum,a.*
                from (
                    select domain_name,count(*) cnt , '%s' as push_type
                     from 
                         %s 
                     where 
                         push_type = '%s'%s
                     group by domain_name 
                     order by 2 desc
                 ) a
               ''' % (str_push_type,view_name,push_type,str_sql)
        #print sql
        cursor.execute(sql)
        rs = cursor.fetchall()
        if len(rs)>=10:
            l = [[rs[i][1],rs[i][2]] for i in range(10)]
        else:
            l = [[x[1],x[2]] for x in rs]
        l_data = rs_to_json(l,)
        s_data = rs_to_json(l,'data')
        print l_data
        print s_data
    return render_template('domain/domain_push_stat_2hz.html',**locals())

@mod.route('/add_role', methods = ['GET', 'POST'])
def add_role():
    if session.get('logged_in'):
        if request.method == 'GET':
            return render_template('domain/input_role_info.html',**locals())
    else:
        return render_template('login.html')

@mod.route('/add_role_json', methods = ['GET', 'POST'])
def add_role_json():
    if session.get('logged_in'):
        if request.method == 'POST':
            role_name = request.form.get('role_name')
            comment = request.form.get('comment')
            try:
                db = conn_db()
                cursor = db.cursor()
                sql = 'select seq_users.nextval from dual'
                cursor.execute(sql)
                role_id = cursor.fetchone()[0]
                sql = '''insert into role(id,role_name,comm) values(:role_id,:role_name,:comm)'''
                cursor.execute(sql,role_id=role_id,role_name=role_name,comm=comment)
                db.commit()
                cursor.close()
                msg = 200
            except Exception,e:
                if 'ORA-00001' in str(e):
                    msg = '增加角色失败,已经存在相同的角色名！'
                else:
                    msg = '增加失败,错误：' + str(e)
            d = {'resultCode':msg}
            j = json.dumps(d)
            return j
    else:
        return render_template('login.html')

@mod.route('/update_role', methods = ['GET', 'POST'])
def update_role():
    if session.get('logged_in'):
        if request.method == 'GET':
            role_id = request.args.get('role_id')
            db = conn_db()
            cursor = db.cursor()
            sql = 'select id,role_name,comm,insert_time from role where id = :role_id'
            cursor.execute(sql,role_id=role_id)
            rs = cursor.fetchone()
            return render_template('domain/update_role_info.html',**locals())
        else:
            db = conn_db()
            cursor = db.cursor()
            role_id = request.form.get('role_id')
            role_name = request.form.get('role_name')
            role_comm = request.form.get('role_comm')
            sql = 'update role set role_name = :role_name,comm = :role_comm where id = :role_id'
            cursor.execute(sql,role_name=role_name,role_comm=role_comm,role_id=role_id)
            db.commit()
            return redirect('/role_admin?signal=update_role')
    else:
        return render_template('login.html')

@mod.route('/update_role_priv',methods = ['GET', 'POST'])
def update_role_priv():
    if session.get('logged_in'):
        if request.method == 'GET':
            role_id = request.args.get('role_id')
            db = conn_db()
            cursor = db.cursor()
            #获取角色名称
            sql = ''' select role_name from role where id = :role_id''' 
            cursor.execute(sql,role_id=role_id)
            rs_role = cursor.fetchone()
            role_name = rs_role[0]
            #获取角色拥有的权限
            sql = ''' select p.id,pp.priv_name ppriv_name,p.priv_name
                      from 
                          privs p,privs pp,priv_role pr
                      where 
                          p.pid = pp.id
                          and p.id = pr.priv_id
                          and pr.role_id = :role_id  
                          order by ppriv_name'''
            cursor.execute(sql,role_id=role_id)
            rs_privs = cursor.fetchall()
            #获取角色未拥有的权限
            sql = ''' select p.id,pp.priv_name ppriv_name,p.priv_name
                      from privs p,privs pp
                      where 
                          p.pid = pp.id
                          and not exists (
                                      select 1 from priv_role pr where role_id = :role_id and pr.priv_id = p.id
                                      )
                          order by ppriv_name
                    '''
            cursor.execute(sql,role_id=role_id)
            rs_privs_no = cursor.fetchall()
            return render_template('domain/update_role_priv.html',**locals())
        else:
            db = conn_db()
            cursor = db.cursor()
            role_id = request.form.get('role_id')
            privs = request.form.get('privs_value')
            l_priv = privs.strip(',').split(',')
            #print 'l_priv===================',l_priv
            sql = 'delete from priv_role where role_id = :role_id'
            cursor.execute(sql,role_id=role_id)
            if len(l_priv)>0:
                for priv_id in l_priv:
                    sql = 'insert into priv_role values(seq_priv_role.nextval,:role_id,:priv_id)'
                    cursor.execute(sql,role_id=role_id,priv_id=priv_id)
                    db.commit()
            else:
                pass
            return redirect('/role_admin?signal=update_role_priv')
    else:
        return render_template('login.html')

@mod.route('/role_delete_json', methods = ['GET', 'POST'])
def role_delete_json():
    if session.get('logged_in'):
        if request.method == 'POST':
            role_id = request.form.get('role_id')
            try:
                db = conn_db()
                cursor = db.cursor()
                sql = '''delete from role where id = :role_id'''
                cursor.execute(sql,role_id=role_id)
                db.commit()
                msg = 200
            except Exception,e:
                msg = '增加角色失败！错误：' + str(e)
            d = {'resultCode':msg}
            j = json.dumps(d)
            return j
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@mod.route('/user_admin')
def user_admin():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        if request.method == 'GET':
            signal = request.args.get('signal')
            sql = '''
                    select id,
                           user_name,
                           email,
                           insert_time,
                           listagg(role_name,',') within group(order by role_name) as role
                    from (
                        select u.id,u.user_name,u.email,u.insert_time,r.role_name 
                        from 
                            users u left join user_role ur 
                            on 
                            u.id = ur.user_id
                            left join role r
                            on ur.role_id = r.id
                        )
                    group by id,user_name,email,insert_time
                    '''
            cursor.execute(sql)
            rs = cursor.fetchall()
            return render_template('domain/user_query.html',**locals())
            # return render_template('domain/tree4_demo.html',**locals())
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')
@mod.route('/update_user',methods = ['GET', 'POST'])
def update_user():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        if request.method == 'GET':
            user_id = request.args.get('user_id')
            db = conn_db()
            cursor = db.cursor()
            sql = 'select id,user_name,email,insert_time from users where id = :user_id'
            cursor.execute(sql,user_id=user_id)
            rs = cursor.fetchone()
            return render_template('domain/update_user_info.html',**locals())
        else:
            db = conn_db()
            cursor = db.cursor()
            user_id = request.form.get('user_id')
            user_name = request.form.get('user_name')
            email = request.form.get('email')
            sql = 'update users set user_name = :user_name,email = :email where id = :user_id'
            cursor.execute(sql,user_name=user_name,email=email,user_id=user_id)
            db.commit()
            return redirect('/user_admin?signal=update_user')
    else:
        return render_template('login.html')

@mod.route('/add_user', methods = ['GET', 'POST'])
def add_user():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        if request.method == 'GET':
            return render_template('domain/input_user_info.html',**locals())
        elif request.method == 'POST':
            sql = 'select seq_users.nextval from dual'
            cursor.execute(sql)
            user_id = cursor.fetchone()[0]
            user_name = request.form.get('user_name')
            email = request.form.get('email')
            password = request.form.get('password1')
            password_md5 = hashlib.md5(password).hexdigest()
            sql = '''insert into users(id,user_name,password,email) values(:user_id,:user_name,:password,:email)'''
            cursor.execute(sql,user_id=user_id,user_name=user_name,password=password_md5,email=email)
            db.commit()
            cursor.close()
            return redirect('/user_admin?signal=add_user')
    else:
        return render_template('login.html')

@mod.route('/delete_user')
def delete_user():
    if session.get('logged_in'):
        if request.method == 'GET':
            db = conn_db()
            cursor = db.cursor()
            user_id = request.args.get('user_id')
            sql = '''delete from users where id = :user_id'''
            cursor.execute(sql,user_id=user_id)
            db.commit()
            cursor.close()
            return redirect('/user_admin?signal=delete_user')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@mod.route('/update_user_role', methods = ['GET', 'POST'])
def update_user_role():
    if session.get('logged_in'):
        if request.method == 'GET':
            db = conn_db()
            cursor = db.cursor()
            user_id = request.args.get('user_id')
            #获取用户名
            sql = 'select user_name from users where id = :user_id'
            cursor.execute(sql,user_id=user_id)
            user_name = cursor.fetchone()[0]
            #获取用户拥有的角色
            sql = '''select id,role_name from role where id in(select role_id from user_role where user_id = :user_id) '''
            cursor.execute(sql,user_id=user_id)
            rs_role = cursor.fetchall()
            #获取用户不拥有的角色
            sql = '''select id,role_name from role r
                     where 
                        not exists 
                            (select 1 from user_role ur where ur.role_id = r.id and ur.user_id = :user_id) 
                    '''
            cursor.execute(sql,user_id=user_id)
            rs_other_role = cursor.fetchall()
            cursor.close()
            return render_template('domain/update_user_role.html',**locals())
        else:
            db = conn_db()
            cursor = db.cursor()
            user_id = request.form.get('user_id')
            privs = request.form.get('privs_value')
            l_priv = privs.strip(',').split(',')
            #print 'l_priv===================',l_priv
            sql = 'delete from user_role where user_id = :user_id'
            cursor.execute(sql,user_id=user_id)
            if len(l_priv)>0:
                for role_id in l_priv:
                    sql = 'insert into user_role values(seq_user_role.nextval,:user_id,:role_id)'
                    cursor.execute(sql,user_id=user_id,role_id=role_id)
                db.commit()
                cursor.close()
            else:
                pass
            return redirect('/user_admin?signal=update_user_role')
    else:
        return render_template('login.html')

@mod.route('/priv_query')
def priv_query():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        if request.method == 'GET':
            return render_template('domain/priv_query.html',**locals())
    else:
        return render_template('login.html')

@mod.route('/get_priv_json')
def get_priv_json():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        username = session['username']
        if request.method == 'GET':
            sql = ''' select id,priv_name from privs where pid = 0'''
            cursor.execute(sql)
            rs = cursor.fetchall()
            l = []
            for row in rs:
                root_id,root_name = row[0],row[1]
                sql = '''select id,priv_name,priv_func from privs where pid = :root_id'''
                cursor.execute(sql,root_id=root_id)
                child_rs = cursor.fetchall()
                d = {'name':root_name,'id':root_id}
                l_child = []
                for child in child_rs:
                    d_child = {'name':child[1],'id':child[0]}
                    l_child.append(d_child)
                d['children'] = l_child
                l.append(d)
            data = json.dumps(l)
        return data 
    else:
        return render_template('login.html')

@mod.route('/domain_tool', methods = ['GET', 'POST'])
def domain_tool(signal=None):
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        sql = '''select DISTINCT domain from domain_tool '''
        cursor.execute(sql)
        rs = cursor.fetchall()
        acs = gs_tool.get_accounts()
        return render_template('domain/domain_tool.html',**locals())
    else:
        return render_template('login.html')

def get_capital_key(lower_dict):
    capital_dict = {}
    for key in lower_dict.keys():
        capital_dict[key.upper()] = lower_dict[key]
    return capital_dict

def get_lower_key(capital_dict):
    lower_dict = {}
    for key in capital_dict.keys():
        lower_dict[key.lower()] = capital_dict[key]
    return lower_dict

@mod.route('/get_update_search', methods = ['GET', 'POST'])
def get_update_search():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        search_domain = request.form.get('dm')
        manage = request.form.get('accounts')
        submit = request.form.get('submit')
        if submit=='godaddy域名同步' and manage:
            gs_tool.update_account(manage)
            domain_gd = gs_tool.get_account_domain(manage)
            sql = 'select DISTINCT domain from domain_tool where manage=:manage'
            cursor.execute(sql,manage=manage)
            column_names = get_column_names(cursor)
            rows = cursor.fetchall()
            domain_sql = []
            for row in rows:
                domain_sql.append(row[0])
            domains_del = set(domain_sql)-set(domain_gd)
            domains_add = set(domain_gd)-set(domain_sql)
            if len(domains_del) != 0:
                for domain in domains_del:
                    sql = 'delete from domain_tool where domain=:domain'
                    cursor.execute(sql,domain=domain)
            if len(domains_add) != 0:
                for domain in domains_add:
                    sql = 'insert into domain_tool (domain,manage) values (:domain,:manage)'
                    cursor.execute(sql,domain=domain,manage=manage)
            db.commit()
        elif submit == '查询' and (search_domain or manage):
            if search_domain and not manage:
                sql = '''select DISTINCT domain from domain_tool where domain=:domain'''
                cursor.execute(sql, domain=search_domain)
            elif manage and not search_domain:
                sql = '''select DISTINCT domain from domain_tool where manage=:manage'''
                cursor.execute(sql, manage=manage)
            else:
                sql = '''select DISTINCT domain from domain_tool where domain=:domain,manage=:manage'''
                cursor.execute(sql, domain=search_domain,manage=manage)
            rs = cursor.fetchall()
            acs = gs_tool.get_accounts()
            return render_template('domain/domain_tool.html',**locals())
        return redirect('/domain_tool')
    else:
        return render_template('login.html')

def get_column_names(cur):
    return [e[0] for e in cur.description]

@mod.route('/edit_domain', methods = ['GET', 'POST'])
def edit_domain(signal=None):
    if session.get('logged_in'):
        domain = request.args.get('domain')
        db = conn_db()
        cursor = db.cursor()
        sql = 'select name,type,data,ttl from domain_tool where domain=:domain'
        cursor.execute(sql,domain=domain)
        column_names = get_column_names(cursor)
        rows = cursor.fetchall()
        domain_sql = []
        for row in rows:
            domain_sql_dict = {}
            for i, column_value in enumerate(row):
                column_name = column_names[i]
                domain_sql_dict[column_name] = column_value
            domain_sql.append(domain_sql_dict)
        userClient = gs_tool.get_user_client(gs_tool.get_domain_account(domain))
        domain_gd = userClient.get_records(domain)
        for domain_dict in domain_gd:
            if domain_dict['type'] in ['A','CNAME','TXT'] and domain_dict['name'] != '_domainconnect':
                if get_capital_key(domain_dict) not in domain_sql:
                    domain_dict['domain'] = domain
                    domain_dict['manage'] = gs_tool.get_domain_account(domain)
                    sql = 'insert into domain_tool (domain,name,type,data,ttl,manage) values (:domain,:name,:type,:data,:ttl,:manage)'
                    cursor.execute(sql,domain=domain,name=domain_dict['name'],type=domain_dict['type'],data=domain_dict['data'],ttl=domain_dict['ttl'],manage=domain_dict['manage'])
        for domain_dict in domain_sql:
            if get_lower_key(domain_dict) not in domain_gd:
                sql = 'delete from domain_tool where domain=:domain and name=:name and data=:data'
                cursor.execute(sql,domain=domain,name=domain_dict['NAME'],data=domain_dict['DATA'])
        db.commit()
        sql = 'select id,name,type,data,manage,domain from domain_tool where domain=:domain'
        cursor.execute(sql, domain=domain)
        rs = cursor.fetchall()
        return render_template('domain/edit_domain.html',**locals())
    else:
        return render_template('login.html')


@mod.route('/edit_domain_dns',  methods = ['GET', 'POST'])
def edit_domain_dns():
    if session.get('logged_in'):
        db = conn_db()
        cursor = db.cursor()
        id = request.form.get('id')
        name = request.form.get('name')
        name_o = request.form.get('name_o')
        type = request.form.get('type')
        type_o = request.form.get('type_o')
        manage = request.form.get('manage')
        domain = request.form.get("domain")
        data = request.form.get('data')
        data_o = request.form.get('data_o')
        submit = request.form.get('submit')
        userClient = gs_tool.get_user_client(manage)
        #print id,name,type,data,domain,manage,submit,name_o,type_o,data_o
        if submit == '保存':
            sql = '''update domain_tool set name=:name,type=:type,data=:data where id=:id'''
            cursor.execute(sql,name=name,type=type,data=data,id=id)
            userClient.delete_records(domain, name_o, type_o, data_o)
            record = {'data': data, 'type': type, 'name': name}
            userClient.add_record(domain, record)
        elif submit == '删除':
            sql = '''delete from domain_tool where id=:id'''
            cursor.execute(sql,id=id)
            userClient.delete_records(domain, name, type, data)
        db.commit()
        #db.close()
        return redirect('/edit_domain?domain=%s' % domain)
        #return render_template('domain/edit_domain.html')
    else:
        return render_template('login.html')

@mod.route('/add_domain_dns',  methods = ['GET', 'POST'])
def add_domain_dns():
    if session.get('logged_in'):
        domain = request.form.get('domain')
        name = request.form.get('name')
        type = request.form.get('type')
        data = request.form.get('data')
        manage = gs_tool.get_domain_account(domain)
        #print domain,name,type,data,manage
        record_sql = {'domain': domain, 'data': data, 'type': type, 'name': name, 'manage':manage}
        gs_tool.insert('domain_tool', record_sql)
        #db.close()
        record = {'data': data, 'type': type, 'name': name}
        userClient = gs_tool.get_user_client(manage)
        userClient.add_record(domain, record)
        return redirect('/edit_domain?domain=%s' % domain)
        #return render_template('domain/edit_domain.html')
    else:
        return render_template('login.html')

@mod.route('/add_account_h')
def add_account_h():
    if session.get('logged_in'):
        return render_template('domain/add_account.html')
    else:
        return render_template('login.html')


@mod.route('/add_gd_account', methods = ['GET', 'POST'])
def add_gd_account():
    if session.get('logged_in'):
        manage = request.form.get('manage')
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        gs_tool.add_account(manage,api_key,api_secret)
        return redirect('/domain_tool')
    else:
        return render_template('login.html')

