from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from config import config_dict, Config
from flask_wtf import CSRFProtect, csrf
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()

# 实例化redis连接对象,用来保存和业务相关的数据,比如图片验证码,短信验证码
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    db.init_app(app)
    Session(app)

    CSRFProtect(app)

    # 生成csrf_token口令，返回给客户端浏览器的cookie中
    # 使用请求勾子(中间件)，在每次请求后，把csrf_token写入客户端的cookie中
    @app.after_request
    def after_request(response):
        csrf_token = csrf.generate_csrf()
        response.set_cookie('csrf_token', csrf_token)  # 把csrf_token设置到浏览器的Set-cookie
        return response

    # 导入home蓝图对象
    from info.modules.home import home_blue, static_blue
    app.register_blueprint(home_blue)
    app.register_blueprint(static_blue)

    # 导入passport蓝图对象
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 导入order蓝图对象
    from info.modules.order import order_blue
    app.register_blueprint(order_blue)

    # 导入profile蓝图对象
    from info.modules.profile import profile_blue
    app.register_blueprint(profile_blue)

    return app