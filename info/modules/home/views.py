from flask import current_app, redirect, g, jsonify, request, session
from info import db
from . import home_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info.utils import constants
from info.models import House, Facility, Area, Order, HouseImage
from info.utils.image_storage import storage


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


@home_blue.route('/api/v1.0/houses', methods=['POST'])
@login_required
def house_release():
    """
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
    """
    user = g.user
    # 获取参数
    title = request.json.get('title')
    price = request.json.get('price')
    area_id = request.json.get('area_id')
    address = request.json.get('address')
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
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days, facility]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 数据类型转换
    try:
        area_id, room_count, acreage, capacity, min_days, max_days = int(area_id), int(room_count), int(acreage), int(
            capacity), int(min_days), int(max_days)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据类型转换失败')
    # 模型类
    new_house = House()
    # 保存数据
    new_house.title = title
    new_house.price = price
    new_house.area_id = area_id
    new_house.address = address
    new_house.room_count = room_count
    new_house.acreage = acreage
    new_house.capacity = capacity
    new_house.beds = beds
    new_house.deposit = deposit
    new_house.min_days = min_days
    new_house.max_days = max_days
    new_house.unit = unit
    new_house.user_id = user.id
    for facility_id in facility:
        f_c_t = Facility.query.filter(facility_id == Facility.id).first()
        new_house.facilities.append(f_c_t)
    try:
        db.session.add(new_house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='房源信息提交失败')
    house_id = new_house.id
    data = {
        'house_id': house_id
    }
    return jsonify(errno=RET.OK, errmsg='个人房源上传成功', data=data)


@home_blue.route('/api/v1.0/areas',methods=['GET'])
def city_list():
    """
    城区列表
    1 从mysql数据库中获取城区列表数据
    2 判断城区列表数据是否获取到
    3 如果获取到遍历数据
    4 以数据列表形式返回前段
    :return:
    """
    try:
        # 从mysql数据库中获取城区列表数据
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取城区数据失败')
    #准备城区数据列表
    area_list = []
    # 遍历数据库获取到的城区信息
    for area in areas:
        # 遍历的字典存入列表
        area_list.append(area.to_dict())
    # 返回前段数据
    return jsonify(errno=RET.OK,errmsg='OK',data=area_list)



@home_blue.route('/api/v1.0/houses/<int:house_id>', methods=["GET"])
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
        user_id = -1
    else:
        user_id = user.id

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.errro(e)
        return jsonify(errno=RET.DBERR, msg='查询房屋信息失败')

    data = {
        'user_id': user_id,
        'house': house.to_full_dict()
    }

    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@home_blue.route('/api/v1.0/houses/<int:house_id>/images', methods=['POST'])
# url: "/api/v1.0/houses/" + house_id + "/images"
@login_required
def house_image(house_id):
    """
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
    """
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
        house = House.query.filter(House.id == house_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房源信息失败')
    # 创建房屋图片模型类对象,将house_id和house_image_name保存到数据库的两个表中
    house_image = HouseImage()
    house_image.house_id = house_id
    house_image.url = house_image_name
    house.index_image_url = house_image_name

    # 提交
    try:
        db.session.add(house_image)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='房屋图片名称提交失败')
    # 拼接地址
    url = constants.QINIU_DOMIN_PREFIX + house_image_name
    data = {
        'url': url
    }
    return jsonify(errno=RET.OK, errmsg='房源图片上传成功', data=data)


# 前端数据通过查询参数获取，方法为get
@home_blue.route('/api/v1.0/houses')
def house_search():
    """
    房屋搜索


    :return:
    """
    area_id = request.args.get('aid')
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    sort_key = request.args.get('sk')
    page = request.args.get('p', 1)
    if area_id:
        try:
            area_id = int(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='数据类型错误')

    if page:
        try:
            page = int(page)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='数据类型错误')

    # 业务处理
    # 排除当前用户发布的房屋
    filters = []
    if 'user_id' in session:
        filters.append(House.user_id != (session['user_id']))
    # 先根据地区ID查找满足条件的房子
    filters.append(House.area_id == area_id)

    # 排序规则,默认根据最新排列
    sort = House.id.desc()
    if sort_key == 'booking':
        sort = House.order_count.desc()
    elif sort_key == 'price-inc':
        sort = House.price.asc()
    elif sort_key == 'price-des':
        sort = House.price.desc()

    try:
        houses_obj = House.query.filter(*filters).order_by(sort)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询房屋错误')

    # 从完成状态的订单中挑选不满足条件房屋，根据id取反
    try:
        orders_obj = Order.query.filter(Order.status != 'REJECTED').all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='订单查询异常')
    # 获取订单中的不满足条件的房屋编号
    orders_list = []
    for order in orders_obj:
        if ((order.begin_date < start_date) and (order.end_date > start_date)) or (
            (order.begin_date >= start_date) and (order.begin_date <= end_date)):
            orders_list.append(order)
    # 筛选
    for order in orders_list:
        for house in houses_obj:
            if order.house_id == house.id:
                houses_obj.remove(house)

    total = 0
    for house in houses_obj:
        total += 1

    houses = []
    for house in houses_obj:
        houses.append(house.to_basic_dict())
    data = {
        'total_page': total,
        'houses': houses
    }
    return jsonify(errno=RET.OK, errmsg='OK', data=data)
