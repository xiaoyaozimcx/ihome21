from info.utils import constants
from info.utils.image_storage import storage
from . import profile_blue
from flask import jsonify, g, current_app, request, redirect, session
from info.utils.commons import login_required
from info import db
from info.utils.response_code import RET
from info.models import User
import re


@profile_blue.route('/api/v1.0/user/auth', methods=['GET'])
@login_required
def get_user_auth():
    """
    获取用户实名信息
    1 判断是否登陆
    2 如果已登陆,查询数据库是否有实名信息
    3 如果没有,正常加载实名页面
    4 如果有实名信息,则返回0和data

    :return:
    """
    user = g.user
    if user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    else:
        data = {
            'real_name': user.real_name,
            'id_card': user.id_card}
        return jsonify(errno=RET.OK, errmsg='OK', data=data)


@profile_blue.route('/api/v1.0/user/auth', methods=['POST'])
@login_required
def set_user_auth():
    # user_id = g.get('user_id')
    # #从前段获取参数
    # fort_end_data = request.get_json()
    # if not fort_end_data:
    #     return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    # real_name = fort_end_data.get('real_name')
    # id_card = fort_end_data.get('id_card')
    # if not all([real_name, id_card]):
    #     return jsonify(errno=RET.PARAMERR, errmsg="信息不完整")
    # if not re.match(r'^[1-9]\d{5}(19|20)\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$', id_card):
    #     return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的身份证号')
    #
    #
    # try:
    #     User.query.filter_by(id=user_id, real_name=None, id_card=None).update(
    #         {"real_name": real_name, "id_card": id_card})
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     db.session.rollback()
    #     return jsonify(errno=RET.SESSIONERR, errmsg="保存用户实名信息失败")
    # return jsonify(errno=RET.OK, errmsg="OK")
    """
    1 判断是否登陆
    2 获取参数
    3 校验参数
    4 保存数据至数据库
    5 返回结果
    :return:
    """
    user = g.user
    if user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    real_name = request.json.get('real_name')
    id_card = request.json.get('id_card')
    user.real_name = real_name
    user.id_card = id_card
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    return jsonify(errno=RET.OK, errmsg='OK')


"""
保存用户头像数据
1.检查用户是否登录
avatar = request.files.get('avatar')
2.检查参数的存在
3.读取文件对象，具有read和write方法的对象
4.把读取道德图片数据给七牛云，实现图片上传
5.保存图片的名称到MySQL中
6.拼接图片地址：七牛云空间域名 +图片名称
7.返回数据给ajaxsubim

"""

@profile_blue.route("/api/v1.0/user/avatar",methods=["POST"])
@login_required
def user_avatar():
    user = g.user
    if user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    #获取参数
    avatar = request.files.get('avatar')
    #判断参数是否存在
    if not avatar:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不存在')

    #读取图片文件
    try:
       image_data = avatar.read()
    except Exception as e:
        current_app.logger(e)
        return jsonify(errno=RET.DATAERR,errmsg='读取图片数据失败')

    #把读取后的数据，传如七牛云
    try:
        image_name =storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='上传图片失败')
    #保存图片数据
    user.avatar_url = image_name
    #提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    #拼接图片的绝对路径，返回前端
    avatar_url = constants.QINIU_DOMIN_PREFIX +image_name
    data = {
        'avatar_url': avatar_url
    }

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data=data)




@profile_blue.route("/api/v1.0/user")
@login_required
def user_info():
    # 判断用户登录
    user = g.user

    if not user:
        return redirect('/')

    avatar_url = user.to_dict()
    data = avatar_url
    return jsonify(errno='0', errmsg='OK', data=data)


"""
个人中心基本页面
1.判断用户是否登录，如果未登录直接重定向到项目首页
2.如果用户已登录，显示用户信息
user = g.user
user.to_dict()
3.调用模型类中的方法，获取用户数据，传入模板

"""

"""
个人中心的个人资料展示和修改用户名
get请求，加载模板页面，post请求修改用户名
1，获取参数name,mobile，avatar_url
2.保存用户信息
3.提交数据到MySQL数据库
4.把缓存中的用户名改掉
5.返回结果

"""


@profile_blue.route('/api/v1.0/user/name', methods=[ 'POST'])
@login_required
def base_info():
    user = g.user

    # post请求，提交数据
    name = request.json.get('name')
    user.name = name
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 修改redis缓存中的数据
    session['nama'] = name

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK')
