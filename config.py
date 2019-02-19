from redis import StrictRedis
class Config:
    DEBUG = None
    # 抽取redis主机和端口号
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/ihome21"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'stPkMpYjBvYF26UsrwxR898oyasgdbX853nOjShiIBZoCHzYKI76cpaRUzdU'
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_dict = {
    'development' : DevelopmentConfig,
    'production' : ProductionConfig
}