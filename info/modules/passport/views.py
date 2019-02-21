from . import passport_blue
from flask import request,jsonify,current_app,make_response,session, g
from info.utils.response_code import RET
from info.utils.captcha.captcha import captcha
from info import redis_store
from info.utils import constants
from info.models import User
import re,random
from info.libs.yuntongxun import sms
from info import db
from info.utils.commons import login_required

# @passport_blue.route('/login')
# def login():
#     return render_template('home/login.html')


@passport_blue.route('/api/v1.0/imagecode')
def generate_image_code():
    '''
       生成图片验证码：

       参数名：cur，验证码编号，str

       1.  利用args在前端地址？后获取uuid，
           前端地址:
            var url = "/api/v1.0/imagecode?cur=" + imageCodeId + "&pre=" + preImageCodeId
       2.  判断uuid是否存在，不存在return
       3.  利用captcha工具，生成图片验证码 （name，text，image）
       4.  把图片验证码内容text存入redis
       5.  把图片image通过makeresponse传给浏览器

       :return:
       '''''
    cur = request.args.get('cur')
    pre = request.args.get('pre',None)
    if not cur:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')

    # a = cur.split('&')
    # cur = a[0]


    # 使用captcha工具生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 把text存入redis数据库中
    try:
        redis_store.setex('ImageCode_' + cur , constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 操作数据库如果发生异常，使用应用上下文对象，记录项目日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    else:
        # 使用响应对象，返回图片
        response = make_response(image)
        # 修改响应的类型
        response.headers['Content-Type'] = 'image/jpg'
        return response


@passport_blue.route('/api/v1.0/smscode', methods=['POST'])
def send_sms_code():
    '''
    发送短信验证码：

    参数名：mobile，手机号，str
           image_code,图片验证码编号，str
           image_code_id，图片验证码内容，str
    获取参数——>校验参数——>业务处理——>返回结果

    1.  从前端获取用户输入的手机号mobile，图片验证码编号image_code,用户输入的图片验证码的内容image_code_id
        var params = {
            "mobile": mobile,
            "image_code": imageCode,
            "image_code_id": imageCodeId
        }
    2.  检查参数是否全部存在
    3.  检查手机号格式，正则
    4.  根据image_code从redis数据库中查询真正的图片验证码内容
        4.1  判断是否获取到图片验证码内容，没有就是图片验证码过期
        4.2  删除redis中真正的图片验证码
        4.3  判断用户输入的图片验证码和真正的图片验证码是否一致
        4.4  判断手机号是否注册
    5.  生成随机短信验证码4位,
    6.  短信验证码存入到redis数据库中
    7.  通过云通讯将短信验证码发送
    8.  判断是否发送成功
    9.  返回结果

    :return:
    '''''
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')  # 用户输入的图片验证码
    image_code_id = request.json.get("image_code_id")  # 前端在发送请求获取图片验证码时，生成的uuid
    # 检查参数的完整性
    # if mobile and image_code_id and image_code:
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 使用正则，校验手机号格式
    # 13112345678
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 图片验证码的校验：必须是先删除，再比较
    # 尝试从redis中获取真实的图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据异常')
    # 判断图片验证码是否过期
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')
    # 把redis中存储的图片验证码删除
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    # 比较图片验证码是否一致，忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
    # 检查手机号是否注册！！！补充
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user is not None:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    # 业务处理
    # 首先生成短信随机数,4位数的字符串
    sms_code = '%04d' % random.randint(0, 9999)
    print(sms_code)
    # 把短信随机数存入redis数据库
    try:
        redis_store.setex("SMSCode_" + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 调用云通讯接口，发送短信，需要保存发送结果
    try:
        ccp = sms.CCP()
        # 第一个参数表示手机号，第二个参数为列表：短信随机码和过期时间，第三个参数表示模板id，免费测试为1
        result = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='发送短信异常')
    # 判断发送结果
    if result == 0:
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送失败')


@passport_blue.route('/api/v1.0/user',methods=['POST'])
def register():
    '''
    用户注册：本质是把用户信息存入mysql数据库
    参数：mobile，手机号
          phonecode，短信验证码
          password，密码
    获取参数——>校验参数——>业务处理——>返回结果
    1.  获取用户输入的手机号mobile，短信验证码phonecode，密码password,确认密码password2
        var mobile = $("#mobile").val()
        var phonecode = $("#phonecode").val()
        var password = $("#password").val()
        var password2 = $("#password2").val()
    2.  判断参数是否完整
    3.  正则判断手机号格式
    4.  从redis中取出真实的短信验证码
    5.  判断获取结果
    6.  检查真实短信验证码与用户输入的验证码是否一致
    7.  删除redis中真实的短信验证码
    8.  判断手机号是否已经注册，查询mysql数据库中是否有用户信息
    9.  判断两次输入的密码是否一致
    10. 密码加密
    11. 把用户信息保存到User表
    12. 提交到mysql
    13. 实现状态保持，用户缓存信息存入到redis
    14. 返回结果
    :return:
    '''''
    mobile = request.json.get('mobile')
    phonecode = request.json.get('phonecode')
    password = request.json.get('password')
    password2 = request.json.get('password2')
    if not all([mobile, phonecode, password,password2]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
        # 检查手机号格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    # 尝试从redis中获取真实短信验证码
    try:
        real_sms_code = redis_store.get('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据失败')
        # 判断获取结果
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg='数据已过期')
    # 先比较短信验证码是否正确
    # sms_code = str(sms_code) 可以对参数进行类型转换，可以进行异常处理
    if real_sms_code != str(phonecode):
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
        # 删除redis中存储的真实短信验证码
    try:
        redis_store.delete('SMSCode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
    # 确认手机号是否注册
    try:
        user = User.query.filter(User.mobile==mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    if password != password2:
        return jsonify(errno=RET.PWDERR, errmsg='两次密码输入不一致')
    user = User()
    user.mobile = mobile
    user.name = mobile
    user.password = password
    # 提交数据到mysql数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        # 保存数据如果失败，需要进行回滚
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 实现状态保持，缓存用户信息
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = mobile
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")

@passport_blue.route('/api/v1.0/session',methods=['POST'])
def login():
    """
    用户登陆
    1/获取参数.mobile  password
    2/检查参数是否完整
    3/使用正则验证手机号格式
    4/根据手机号确认用户是否存在
    5/校验密码
    6/保存用户登录时间
    7/提交数据到mysql
    8/返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    # 检查参数的完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失' )
    # 检查手机号格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.DATAERR,errmsg='手机格式错误')
    # 根据手机号检查用户是否注册过
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        assert isinstance(current_app, object)
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询用户失败')
    # # 判断查询结果
    # if not user:
    #     return jsonify(errno=RET.NODATA,errmsg='用户未注册')
    # # 检查密码是否正确
    # if not user.check_passowrd(password):
    #     return jsonify(errno=RET.PWDERR,errmsg='密码错误')

    # 用户是否存在和密码正确，建议在一起判断，返回前端一个模糊的错误信息
    if not user or not user.check_password(password):
        return jsonify(errno=RET.ROLEERR, errmsg='用户名或密码错误')
    # 保存登录时间
    # user.last_login = datetime.now()

    # 提交数据到mysql
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.THIRDERR,errmsg='保存数据失败')
    # 实现状态保持
    session['user_id'] = user.id
    session['mobile'] = user.mobile
    # 因为用户会多次登录，有可能会修改昵称，如果修改了为修改后的昵称，否则，昵称为手机号
    session['name'] = user.name
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='登陆成功')



@passport_blue.route('/api/v1.0/session', methods=['GET'])
@login_required
# 获取登陆状态,显示右上角登陆信息
def logging_status():
    """
    一、页面右上角用户信息展示，检查用户登录状态，如果用户已经登录，显示用户信息，
    否则提供登录注册入口！
    1.1尝试从redis中获取用户缓存的用户信息，获取user_id
    1.2如果有user_id, 根据id查询mysql，获取用户信息
    1.3如果查询到用户信息，返回用户信息给模板
    """
    # user_id = session.get('user_id')
    # user_mobile = session.get('mobile')
    # user_name = session.get('name')
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user.mobile)
    #     except Exception as e:
    #         current_app.logger.error(e)
    #
    #     data = {
    #         'user_id':user_id,
    #         'name':user_name if user_name else None,
    #         'user_info': user_mobile if user_mobile else None
    #
    #     }
    #     return jsonify(errno='0', errmsg='OK', data=data)
    # else:
    #     return jsonify(errno=RET.SESSIONERR, errmsg='未登录')
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    else:
        data = {
            "name": user.name,
            "user_id": user.id
        }
        return jsonify(errno=RET.OK, errmsg='OK', data=data)




@passport_blue.route('/api/v1.0/session',methods=['DELETE'])
def logout():
    """
    用户退出
    1、退出的本质是把服务器缓存的用户信息清除
    2、使用session对象清除用户信息

    补充：
    如果是前后端分离项目，退出登录请求方法为delete
    """
    session.pop('user_id',None)
    session.pop('name',None)
    session.pop('mobile',None)
    return jsonify(errno=RET.OK,errmsg='OK')