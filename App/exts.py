# 存放插件

# 扩展第三方插件
from  flask_sqlalchemy import  SQLAlchemy
from  flask_migrate import Migrate
from flask_cors import CORS

# 2 初始化
db = SQLAlchemy()
migrate = Migrate() #数据迁移
# 3 和app绑定

def init_exts(app):
    CORS(app)  # 允许所有域名的跨域请求
    db.init_app(app=app)
    migrate.init_app(app=app,db=db)