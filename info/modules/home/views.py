from flask import current_app, redirect, g, jsonify,request
from . import home_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info.models import House,Facility
from info.utils import constants
from info.utils.image_storage import storage
from info import db

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


@home_blue.route('/api/v1.0/houses',methods= ['POST'])
@login_required
def house_release():
    '''
    个人房源发布：
    获取参数/校验参数/业务处理/返回结果

    1.  判断用户是否登录
    2.  获取参数title,price,area_id,adress,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days,facility
    3.  校验参数
    4.  数据类型转换
    5.  房源内容保存到数据库
    6.  提交
    7.  返回house_id

    :return:
    '''''
    user = g.user
    # 获取参数
    title = request.json.get('title')
    price = request.json.get('price')
    area_id = request.json.get('area_id')
    adress = request.json.get('adress')
    room_count = request.json.get('room_count')
    acreage = request.json.get('acreage')
    capacity = request.json.get('capacity')
    beds = request.json.get('beds')
    deposit = request.json.get('deposit')
    min_days = request.json.get('min_days')
    max_days = request.json.get('max_days')
    facility = request.json.get('facility')
    unit = request.json.get('unit')

    # 校验
    if not all([title,price,area_id,adress,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days,facility]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 数据类型转换
    try:
        area_id, room_count, acreage, capacity, min_days, max_days = int(area_id), int(room_count), int(acreage), int(capacity), int(min_days),int(max_days)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据类型转换失败')
    # 模型类
    new_house = House()
    # 保存数据
    new_house.title = title
    new_house.price = price
    new_house.area_id = area_id
    new_house.address = adress
    new_house.room_count = room_count
    new_house.acreage = acreage
    new_house.capacity = capacity
    new_house.beds = beds
    new_house.deposit = deposit
    new_house.min_days = min_days
    new_house.max_days = max_days
    new_house.unit = unit
    for facility_id in facility:
        facilities = Facility.query.filter_by(facility_id == Facility.id).first()
        new_house.facilities.append(facilities)
    try:
        db.session.add(new_house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='房源信息提交失败')
    house_id = new_house.id
    data = {
        'house_id' : house_id
    }
    return jsonify(errno=RET.OK, errmsg='个人房源上传成功',data = data)


@home_blue.route('/api/v1.0/houses/<int:house_id>/images',methods=['POST'])
# url: "/api/v1.0/houses/" + house_id + "/images"
@login_required
def house_image(house_id):
    '''
    上传房源图片：

    获取参数/校验参数/业务处理/返回结果
    参数：house_image,图片文件，file
    返回结果：url，用户上传成功后的房源图片的地址

    1.  检查用户是否登录
    2.  获取参数：用户上传的房屋图片(house_image)
    3.  校验参数是否完整
    4.  读取文件
    5.  读取到的数据给七牛云，上传图片
    6.  保存七牛云返回的图片名称到mysql
    7.  拼接图片真正地址=七牛云空间域名+图片名称
    8.  返回到前端

    :return:
    '''''
    pass
    user = g.user
    # 获取用户上传de图片
    house_image = request.files.get('house_image')
    if not house_image:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 读取图片文件
    try:
        house_image_data = house_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='读取图片文件失败')
    # 文件上传到七牛云
    try:
        house_image_name = storage(house_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片异常')
    try:
        # 根据房屋id获取房源信息
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房源信息失败')
    # 房屋图片名称保存到数据库
    house.images = house_image_name
    # 提交
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='房屋图片名称提交失败')
    # 拼接地址
    url = constants.QINIU_DOMIN_PREFIX + house_image_name
    data = {
        'url':url
    }
    return jsonify(errno=RET.OK, errmsg='房源图片上传成功',data=data)

