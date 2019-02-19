from . import profile_blue
from flask import jsonify,g,current_app,request
from info.utils.commons import login_required
from info import db
from info.utils.response_code import RET
from info.models import  User
import re

@profile_blue.route('/api/v1.0/user/auth',methods=['GET'])
@login_required
def get_user_auth():
    user = g.user
    if  user is None:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    if user.real_name and user.id_card:
        data = {
            'real_name':user.real_name,
            'id_card':user.id_card}
        return jsonify(errmo=RET.OK, errmsg='OK', data=data)

@profile_blue.route('/api/v1.0/user/auth',methods=['POST'])
@login_required
def set_user_auth():
    user_id = g.get('user_id')
    #从前段获取参数
    fort_end_data = request.get_json()
    if not fort_end_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    real_name = fort_end_data.get('real_name')
    id_card = fort_end_data.get('id_card')
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="信息不完整")
    if not re.match(r'^[1-9]\d{5}(19|20)\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$', id_card):
        return jsonify(errno = RET.PARAMERR,errmsg = '请输入正确的身份证号')


    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None).update(
            {"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.SESSIONERR, errmsg="保存用户实名信息失败")
    return jsonify(errno=RET.OK, errmsg="OK")


