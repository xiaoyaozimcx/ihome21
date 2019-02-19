from flask import current_app, redirect
from . import home_blue

@home_blue.route('/')
def index():
    return redirect('/index.html')


@home_blue.route('/favicon.ico')
def favicon():
    # send_static_file函数是flask框架自带的函数,作用是把具体的文件发送给浏览器
    return current_app.send_static_file('favicon.ico')

