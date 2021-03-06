#!/usr/local/bin/python
# -*- coding: utf-8
import sys
sys.path.append("..")
from utils.conn_mysql import conn_mysql
from utils.tools import *
from flask import Flask,url_for
from flask import render_template,Blueprint,abort
from flask import request,flash, redirect,session
from jinja2 import TemplateNotFound
from flask_login import LoginManager
reload(sys)
sys.setdefaultencoding('utf-8')

#加密存储密码
import os
import hashlib
def encrypt_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).encode('hex') # length 32
    result = password
    for i in range(3):
        result = hashlib.sha256(password + salt).hexdigest()[::2] #length 32
    return result, salt


mod = Blueprint('user', __name__,template_folder='templates')

@mod.route('/')
def home(message = ''):
    if not session.get('logged_in'):
        return render_template('login.html',message = message)
    else:
        username = session['username']
        return redirect(url_for('user.index',username = username))

@mod.route('/index')
def index():
    if session.get('logged_in'):
        username = session['username']
        l_privs = get_user_privs(username)
        print 'l_privs====',l_privs
        return render_template('index.html',**locals())
    else:
        return render_template('login.html')


@mod.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if not session.get('logged_in'):
            return render_template('login.html',message = '')
        else:
            username = session['username']
            return redirect(url_for('user.index',username = username))
    else:
        username = request.form['username']
        password = request.form['password']
        password_md5 = hashlib.md5(password).hexdigest()
        message = ''
        #user = [username,password]
        sql = '''select user_name,password,email from users where user_name = \''''\
              + username + '''\' and password =\'''' + password_md5 +'''\''''
        db = conn_db()
        cursor = db.cursor()
        cursor.execute(sql)
        rs = cursor.fetchall()
        cursor.close()
        db.close()
        if len(rs) > 0:
            session['logged_in'] = True
            session['username'] = username
        else:
            session['logged_in'] = False
            message = u'错误的用户名或密码！'
        return home(message)

@mod.route('/logout')
def logout():
    session['logged_in'] = False
    session['record_count'] = None
    return home()





