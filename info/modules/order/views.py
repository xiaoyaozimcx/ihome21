from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask import url_for

from info import db, redis_store
from info.utils.commons import login_required

from info.models import Order, House
from info.utils.response_code import RET
from . import order_blue
from flask import jsonify
from datetime import datetime


@order_blue.route('/api/v1.0/orders', methods=['POST'])
@login_required
def booking():
    '''
    1.判断用户是否登陆
    2.获取用户订单id：order_id
    3.获取房屋id：house_id
    4.获取房屋的单价:house_price
    5.校验开始日期start_date和结束日期end_date
    6.验证参数的完整性
    7.计算预订的总天数：days = end_date - start_date
    8.计算订单的总金额: house_price * days
    9.返回数据
    :return:
    '''
    # 判断用户是否登录
    user = g.user
    # 获取用户订单id：order_id
    if not user:
        return jsonify(errno=RET.DBERR, errmsg='用户未登陆')
        # return redirect('/login.html')
        # return redirect(url_for('/login'))

    # 获取参数
    house_id = request.json.get('house_id')
    start_date_str = request.json.get('start_date')
    end_date_str = request.json.get('end_date')
    # house_price = request.json.get('')
    # 判断参数完整性
    if not all([house_id, start_date_str, end_date_str]):
        return jsonify(errno=RET.DBERR, errmsg='参数缺失')
    # 转换数据类型
    # 转换数据类型
    house_id = int(house_id)
    try:
        start_date = datetime.strptime(start_date_str,'%Y-%m-%d')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='日期类型转换失败')
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='日期类型转换失败')



    # 计算入住总日期
    days = (end_date - start_date).days+1

    # 获取房屋单价
    house = House.query.get(house_id)
    house_price = house.price
    # 总价
    amount = days*house_price

    # 保存到数据库
    order = Order()
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.user_id = user.id
    order.days = days
    order.house_price = house_price
    order.amount = amount
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    data = {
        'order_id': order.id
    }
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


#

'''
二、获取订单列表
1.判断用户是否登陆
2.判断role是房客custom还是房东landlord
	2.1 如果是房客，重定向到我的订单：orders.html
	2.2 如果是房东，重定向到客户订单：lorders.html
3.顶以订单列表
	3.1 获取订单金额：amount
	3.2 获取订单评论/拒单原因：
		3.2.1 如果role == cusrom， 获取拒单原因
		3.2.2 如果role == landlord, 获取订单评论
	3.3 获取创建时间:ctime
	3.4 获取入住天数:days
	3.5 获取入住日期:start_date
	3.6 获取离开日期:end_date
	3.7 获取房屋图片地址:img_url
	3.8 获取订单id:order_id
	3.9 获取订单状态:status
	3.10 获取房屋标题:title
4. 返回数据
'''
@order_blue.route('/api/v1.0/orders')
@login_required
def get_booking():
    # 判断用户是否登陆
    user = g.user
    if not user:
        # current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='用户未登录')
    role = request.args.get('role')
    # 校验参数
    if role not in ["custom", "landlord"]:
        # current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='参数获取错误')
    # 查询订单数据
    # 判断是什么类型
    if role == 'landlord':
        # 房东类型
        house = House.query.filter(House.user_id == user.id).all()
        # 获取房东有的所有房子
        house_all_id = [hs.id for hs in house]
        # 按照时间倒叙显示用户下的订单
        orders = Order.query.filter(Order.house_id.in_(house_all_id)).order_by(Order.begin_date.desc()).all()
    else:
        orders = Order.query.filter(Order.user_id == user.id).order_by(Order.begin_date.desc()).all()
    # 定义一个列表用来存储订单数据
    orders_list = []
    # 通过循环遍历获取数据
    for order in orders:
        orders_list.append(order.to_dict())

    #返回数据
    data = {
        'orders':orders_list
    }

    return jsonify(errno=RET.OK, errmsg='OK', data=data)




#评论功能
'''
三. 接单和拒单
1.判断用户是否登陆
	1.2 判断是否是房东
2.获取订单号
3.判断是否拒单
	3.1拒单时返回原因
4.返回数据
'''
@order_blue.route('/api/v1.0/orders', methods = ['PUT'])
@login_required
def orders_comments():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 获取参数
    action = request.json.get('action')
    order_id = request.json.get('order_id')
    reason = request.json.get('reason')
    # 判断参数完整性
    if not all([action, order_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 检查参数
    if action not in ['accept', 'reject']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不对')
    # 查询未处理的订单
    order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
    # 判断参数类型
    if action == 'accept':
        order.status = "WAIT_COMMENT"
    else:
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='没有拒单原因')
        order.status = "REJECTED"
        order.comment = reason
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.OK, errmsg='保存数据失败')

    return jsonify(errno=RET.OK, errmsg='OK')





@order_blue.route('/api/v1.0/orders/comment', methods=['PUT'])
@login_required
def save_order_comment():
    # 查看用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 获取参数
    comment = request.json.get("comment")
    order_id = request.json.get("order_id")

    # 二. 校验参数
    # 要求用户必须填写评论内容
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        order_id = int(order_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.SERVERERR, errmsg='处理参数错误')

    # 三. 业务逻辑处理
    # 3.1 查询订单状态为待评价
    try:
        # 根据订单id/订单所属用户/订单状态为待评价状态
        order = Order.query.filter(Order.id == order_id, Order.user_id == user.id,
                                   Order.status == "WAIT_COMMENT").first()
        # 查询订单所属房屋
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")
    # 校验查询结果
    if not order:
        return jsonify(errno=RET.REQERR, errmsg="操作无效")

    # 3.2 保存评价信息
    try:
        # 将订单的状态设置为已完成
        order.status = "COMPLETE"
        # 保存订单的评价信息
        order.comment = comment
        # 将房屋的完成订单数增加1,如果订单已评价,让房屋成交量加1
        house.order_count += 1
        # add_all可以一次提交多条数据db.session.add_all([order,house])
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 提交数据,如果发生异常,进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    # 3.3 缓存中存储的房屋信息,因为订单成交,导致缓存中的数据已经过期,所以,需要删除过期数据
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK")













