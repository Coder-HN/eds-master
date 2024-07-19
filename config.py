class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/edsystem'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/edsystem'
    TESTING = True
