from flask import current_app, redirect, g, jsonify
from . import home_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info.utils import constants
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


@home_blue.route('/api/v1.0/houses/index')
@login_required
def home_page_image():
    """
    1 查询数据库,过滤筛选创建时间倒序排序,limit前5个House对象
    2 判断是否拿到数据
    3 创建空列表data
    4 遍历筛选的House对象,转成字典格式,添加到data中
    5 返回结果

    :return:
    """
    # 查询数据库,过滤筛选
    try:
        home_image_list = House.query.order_by(House.create_time.desc()).limit(constants.HOME_PAGE_MAX_IMAGES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常')
    # 判断是否拿到数据
    if home_image_list is None:
        return jsonify(errno=RET.NODATA, errmsg='数据不存在')
    # 创建data
    data = []
    # 遍历home_image_list,转换字典格式,添加到data中
    for home in home_image_list:
        try:
            data.append(home.to_basic_dict())
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据异常')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data=data)

