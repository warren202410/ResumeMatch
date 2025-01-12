class Config:
    UPLOAD_FOLDER = 'uploads'
    RECOGNIZED_FOLDER = 'recognized'
    PARSED_FOLDER = 'parsed'

    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'pdf', 'gif', 'bmp', 'tiff', 'webp', 'doc', 'docx',
        'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'odt', 'ods', 'odp', 'zip',
        'rar', '7z', 'tar', 'gz', 'mp3', 'wav', 'mp4', 'avi', 'mkv','json'
    }

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    MAX_WORKERS = 5

    # OPENAI_API_KEY = ""
