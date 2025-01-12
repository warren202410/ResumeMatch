from flask import Blueprint

# 创建一个名为 'main' 的蓝图
main = Blueprint('main', __name__)

# 导入该蓝图的路由定义
from app.main import routes