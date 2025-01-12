from app import create_app
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    设置日志配置，包括控制台日志和文件日志。
    使用RotatingFileHandler来处理日志文件的滚动，防止日志文件过大。
    """
    # 配置基本日志级别
    logging.basicConfig(level=logging.DEBUG)

    # 创建一个日志处理器，处理日志文件的滚动
    handler = RotatingFileHandler('app.log', maxBytes=10 * 1024 * 1024, backupCount=10,encoding='utf-8')

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 获取根日志记录器并添加处理器
    logging.getLogger().addHandler(handler)


# 初始化日志设置
setup_logging()

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 启动Flask应用，启用调试模式
    app.run(debug=True,host='0.0.0.0',port=5004)
