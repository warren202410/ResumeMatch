# app/utils/allowed_file.py
from app import Config


def allowed_file(filename, app_config):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
