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



@home_blue.route('/houses/<int:house_id>', methods=["GET"])
@login_required
def detail_house(house_id):
    """
    房屋详情
    1,建立视图函数，需要前端给后端返回房屋的ID
    2，从g对象中获取用户信息，如果获取不到用户对象则返回user_id为-1
    3，根据传入的hoser_id在数据库中查询house信息
    4，house对象调用模板函数，将数据库查询到的信息保存到字典中
    5，将信息返回给前段页面

    """
    user = g.user
    if not user:
        return user['user_id'] == -1
    else:
        user_id = user.id

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.errro(e)
        return jsonify(errno = RET.DBERR, msg = '查询房屋信息失败')


    data = {
        'user_id':user_id,
        'house_data':house.to_full_dict()
    }

    return jsonify(errno = RET.OK, errmsg = 'OK' , data = data)



