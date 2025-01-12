from flask import Flask
from app.config import Config

from flask_cors import CORS

def create_app(config_class=Config):
    """
    创建并配置Flask应用。

    参数:
        config_class (class): 配置类，默认使用Config类。

    返回:
        app (Flask): 配置好的Flask应用实例。
    """
    # 创建Flask应用实例，指定静态文件夹和模板文件夹
    app = Flask(__name__, static_folder='static', template_folder='templates')

    # 启用跨域资源共享（CORS）
    CORS(app)

    # 从配置类加载配置
    app.config.from_object(config_class)

    # 注册主蓝图，并指定URL前缀
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')

    return app
