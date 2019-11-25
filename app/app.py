#!/usr/local/bin/python
# -*- coding: utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
#import views.oracle
import views.agent
import views.user
import views.user_stats
import views.test
import views.domain
from flask_login import LoginManager
from flask import Blueprint
import chartkick
import os

app = Flask(__name__)
app.debug = True
app.register_blueprint(views.user.mod)
app.register_blueprint(views.agent.mod)
app.register_blueprint(views.user_stats.mod)
app.register_blueprint(views.test.mod)
app.register_blueprint(views.domain.mod)

# ck = Blueprint('ck_page', __name__, static_folder=chartkick.js(), static_url_path='/static/Scripts')
# app.register_blueprint(ck, url_prefix='/ck')
# app.jinja_env.add_extension("chartkick.ext.charts")

# login_manager = LoginManager()
# login_manager.init_app(app)

# login_manager.session_p_view = "login.login_page" #login view的名字
# login_manager.login_message = u'提示信息。'
# rotection = "strong" #这里指定为strong，默认为'basic'
# login_manager.login
app.secret_key = os.urandom(12)
app.config['SESSION_TYPE'] = 'filesystem'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://scott:tiger@localhost/mydatabase?charset=utf8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle://hgame:ora_0046@10.20.1.151:1521/bidb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
class user(db.Model):
	id = db.Column(db.Integer,primary_key=True)
	username = db.Column(db.String(80),unique=True,nullable=False)
	email = db.Column(db.String(120),unique=True,nullable=False)
	def __repr__(self):
		return '<User %r>' % self.username
if __name__ == '__main__':
    app.run(host='0.0.0.0',threaded=True)
