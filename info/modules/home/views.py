from flask import current_app, redirect, g, jsonify
from . import home_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info.models import House

@home_blue.route('/')
def index():
    return redirect('/index.html')


@home_blue.route('/favicon.ico')
def favicon():
    # send_static_file函数是flask框架自带的函数,作用是把具体的文件发送给浏览器
    return current_app.send_static_file('favicon.ico')


@home_blue.route('/api/v1.0/user/houses')
@login_required
def my_houses_list():
    """
    我的房屋发布列表:
    1 判断用户是否已登陆
    2 判断用户是否实名认证
    3 如果实名认证,获取数据库该房东相关房屋信息
    4 返回结果和data

    :return:
    """
    # 判断用户是否已登陆
    user = g.user
    if not user:
        return redirect('/index.html')
    # 判断用户是否实名认证
    try:
        real_name = user.real_name
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常')
    # 如果实名认证,查询该房东所有房屋信息并排序,遍历添加到列表
    if real_name:
        try:
            houses = House.query.filer(House.user_id == user.id).order_by(House.create_time.desc()).all()
        except Exception as e:
            current_app.logger.error(e)
        data = []
        for house in houses:
            data.append(house.to_basic_dict())
    # 返回结果
        return jsonify(errno=RET.OK, errmsg='OK', data=data)