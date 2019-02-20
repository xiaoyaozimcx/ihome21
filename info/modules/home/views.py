from flask import current_app, redirect, g, jsonify
from . import home_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info.models import House, Area


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
    1 获取数据库该房东相关房屋信息
    2 遍历,并以字典格式添加至data列表
    3 返回结果和data

    :return:
    """

    user = g.user

    try:
        houses = House.query.filter(House.user_id == user.id).order_by(House.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常')

    data = []
    for house in houses:
        data.append(house.to_basic_dict())
# 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data=data)

@home_blue.route('/api/v1.0/areas', methods=['GET'])
def city_list():
    """
    城区列表
    1 从数据库获取城区数据areas
    2 判断是否获得数据
    3 根据js文件要求，整合成数据列表发送给前段
    :return:
    """
#     # aid = user.query.get['aid']
#     # data = [{"aid":aid,"aname":"aname"}]
#     # return jsonify(errno=RET.OK,errmsg='OK',data=data)
#     # pass
#     try:
#         areas = Area.query.all()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='查询地区错误')
#
#     area_list = []
#     for area in areas:
#         area_list.append(area.to_dict())
#
#     return jsonify(errno=RET.OK, errmsg='OK', data=area_list)
    try:
        #从mysql中获取城区数据
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询地区错误')
    # 先准备城区数据列表
    area_list = []
    for area in areas:
        #把遍历出的数据字典添加到城区列表中
        area_list.append(area.to_dict())
    # 如果ok，返回数据列表data给前段
    return jsonify(errno=RET.OK, errmsg='OK', data=area_list)

