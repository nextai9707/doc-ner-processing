# __init__.py 初始化文件创建Flask应用
import pymysql
import os
from dotenv import load_dotenv
from .exts import  init_exts
from flask import Flask
from . import *
from .views import blus

# 加载环境变量
load_dotenv()

def create_app():
    # 配置静态文件夹和模板文件夹
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    front_dist = os.path.join(base_dir, 'front', 'dist')
    
    app = Flask(__name__)
    
    # 从环境变量读取数据库配置
    HOSTNAME = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', 3306))
    USERNAME = os.getenv('DB_USERNAME', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '123456')
    DATABASE = os.getenv('DB_DATABASE', '')
    # 通过修改以下代码来操作不同的SQL比写原生SQL简单很多 --》通过ORM可以实现从底层更改使用的SQL
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
    
    # 注册蓝图（API路由，必须在静态文件路由之前）
    app.register_blueprint(blueprint=blus)
    
    # 初始化插件
    init_exts(app=app)
    
    # 配置静态文件服务（如果dist目录存在）
    if os.path.exists(front_dist):
        from flask import send_from_directory, send_file
        
        # 静态资源文件路由（必须在通用路由之前）
        @app.route('/assets/<path:filename>')
        def static_assets(filename):
            """提供静态资源文件（JS、CSS等）"""
            assets_dir = os.path.join(front_dist, 'assets')
            if os.path.exists(os.path.join(assets_dir, filename)):
                return send_from_directory(assets_dir, filename)
            return {'error': 'File not found'}, 404
        
        # 其他静态文件（如favicon.ico等）
        @app.route('/favicon.ico')
        @app.route('/<path:filename>')
        def serve_static_or_spa(filename='index.html'):
            """提供静态文件或SPA路由"""
            # 排除API路由（这些应该已经被蓝图处理了）
            if filename.startswith('api/') or filename.startswith('sys/'):
                return {'error': 'Not found'}, 404
            
            # 如果是favicon.ico
            if filename == 'favicon.ico':
                favicon_path = os.path.join(front_dist, 'favicon.ico')
                if os.path.exists(favicon_path):
                    return send_file(favicon_path)
                return '', 204
            
            # 检查是否是实际存在的文件
            file_path = os.path.join(front_dist, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return send_from_directory(front_dist, filename)
            
            # 否则返回index.html（SPA路由）
            return send_from_directory(front_dist, 'index.html')
        
        # 根路由
        @app.route('/')
        def index():
            """返回前端首页"""
            return send_from_directory(front_dist, 'index.html')
    else:
        # 如果dist目录不存在，提供一个提示页面
        @app.route('/')
        def index():
            return '''
            <html>
                <head><title>前端未构建</title></head>
                <body>
                    <h1>前端未构建</h1>
                    <p>请先构建前端项目：</p>
                    <pre>cd front && pnpm build</pre>
                </body>
            </html>
            ''', 200
    
    return  app