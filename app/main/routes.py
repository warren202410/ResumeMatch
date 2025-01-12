import json
import os
import traceback

import requests
from flask import request, jsonify

from app import Config
from app.main import main
from app.main.services.report_service import generate_job_match_report
from app.main.services.resume_service import clean_data
from app.main.services.score_service import calculate_education_score, calculate_skills_score, \
    calculate_experience_score, calculate_project_score

from app.utils.allowed_file import allowed_file
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

from app.utils.helpers import gpt4_parse_jd_to_json, client


# @main.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'success': False, 'message': '请求中没有文件部分'}), 400
#
#     file = request.files['file']
#
#     if file.filename == '':
#         return jsonify({'success': False, 'message': '未选择任何文件'}), 400
#
#     if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
#         return jsonify({'success': False, 'message': '不允许的文件类型'}), 400
#
#     try:
#         if not os.path.exists(Config.UPLOAD_FOLDER):
#             os.makedirs(Config.UPLOAD_FOLDER)
#
#         filename = file.filename
#         file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
#         file.save(file_path)
#
#         return jsonify({'success': True, 'message': '文件上传成功', 'file_path': file_path})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500
#
#
# @main.route('/recognize', methods=['POST'])
# def recognize_file():
#     data = request.get_json()
#     file_path = data.get('file_path')
#
#     if not file_path or not os.path.exists(file_path):
#         return jsonify({'success': False, 'message': '文件路径无效或文件不存在'}), 400
#
#     try:
#         if not os.path.exists(Config.RECOGNIZED_FOLDER):
#             os.makedirs(Config.RECOGNIZED_FOLDER)
#
#         recognized_file_path = os.path.join(Config.RECOGNIZED_FOLDER, os.path.basename(file_path) + '.txt')
#
#         # Initialize the docTR OCR model
#         model = ocr_predictor(pretrained=True)
#
#         # Load the document (PDF or image)
#         doc = DocumentFile.from_pdf(file_path)  # 使用 docTR 的方法加载 PDF 文件
#
#         # Perform OCR
#         result = model(doc)
#
#         # Extract the recognized text using render()
#         document_text = result.render()  # 使用 render() 导出识别的内容
#
#         # Save the recognized text to a file
#         with open(recognized_file_path, 'w', encoding='utf-8') as f:
#             f.write(document_text)
#
#         if not document_text:
#             return jsonify({'success': False, 'message': '文本识别失败'}), 500
#
#         return jsonify({'success': True, 'message': '文本识别成功', 'recognized_file_path': recognized_file_path})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500
#
#
# @main.route('/parse', methods=['POST'])
# def parse_file():
#     data = request.get_json()
#     recognized_file_path = data.get('recognized_file_path')
#
#     if not recognized_file_path or not isinstance(recognized_file_path, str) or not os.path.exists(
#             recognized_file_path):
#         return jsonify({'success': False, 'message': '识别文件路径无效或文件不存在'}), 400
#
#     try:
#         if not os.path.exists(Config.PARSED_FOLDER):
#             os.makedirs(Config.PARSED_FOLDER)
#
#         with open(recognized_file_path, 'r', encoding='utf-8') as text_file:
#             resume_text = text_file.read()
#
#         # 调用 clean_data 进行简历解析
#         parsed_resume = clean_data(resume_text, '简历', Config.OPENAI_API_KEY)
#         if parsed_resume is None:
#             return jsonify({'success': False, 'message': '简历解析失败'}), 500
#
#         # 生成解析文件的路径，保留原始文件名，但扩展名改为 .json
#         parsed_file_name = os.path.splitext(os.path.basename(recognized_file_path))[0] + '.json'
#         parsed_file_path = os.path.join(Config.PARSED_FOLDER, parsed_file_name)
#
#         # 将解析后的数据保存为JSON文件
#         with open(parsed_file_path, 'w', encoding='utf-8') as json_file:
#             json.dump(parsed_resume, json_file, ensure_ascii=False, indent=4)
#
#         return jsonify({'success': True, 'message': '简历解析成功', 'parsed_file_path': parsed_file_path,
#                         'parsed_content': parsed_resume})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/process_resume', methods=['POST'])
def process_resume():
    data = request.get_json()
    file_url = data.get('file_url')

    if not file_url:
        return jsonify({'success': False, 'message': '文件URL无效'}), 400

    try:
        # 下载远程文件
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({'success': False, 'message': '无法下载文件'}), 400

        # 临时保存下载的文件
        temp_file_path = os.path.join(Config.UPLOAD_FOLDER, os.path.basename(file_url))
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)

        # 确保识别和解析文件夹存在
        if not os.path.exists(Config.RECOGNIZED_FOLDER):
            os.makedirs(Config.RECOGNIZED_FOLDER)
        if not os.path.exists(Config.PARSED_FOLDER):
            os.makedirs(Config.PARSED_FOLDER)

        # Step 1: 识别文本内容
        recognized_file_path = os.path.join(Config.RECOGNIZED_FOLDER, os.path.basename(temp_file_path) + '.txt')

        # Initialize the docTR OCR model
        model = ocr_predictor(pretrained=True)

        doc = DocumentFile.from_pdf(temp_file_path)

        # Load the document (PDF or image)
        # if temp_file_path.lower().endswith('.pdf'):
        #     doc = DocumentFile.from_pdf(temp_file_path)
        # else:
        #     doc = DocumentFile.from_images(temp_file_path)

        # Perform OCR
        result = model(doc)

        # Extract the recognized text using render()
        document_text = result.render()

        # Save the recognized text to a file
        with open(recognized_file_path, 'w', encoding='utf-8') as f:
            f.write(document_text)

        if not document_text:
            return jsonify({'success': False, 'message': '文本识别失败'}), 500

        # Step 2: 解析文本内容为标准JSON格式
        parsed_resume = clean_data(document_text, '简历', Config.OPENAI_API_KEY)
        if parsed_resume is None:
            return jsonify({'success': False, 'message': '简历解析失败'}), 500

        # 生成解析文件的路径，保留原始文件名，但扩展名改为 .json
        parsed_file_name = os.path.splitext(os.path.basename(temp_file_path))[0] + '.json'
        parsed_file_path = os.path.join(Config.PARSED_FOLDER, parsed_file_name)

        # 将解析后的数据保存为JSON文件
        with open(parsed_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(parsed_resume, json_file, ensure_ascii=False, indent=4)

        # 删除临时文件
        os.remove(temp_file_path)

        # 返回解析后的JSON数据
        return jsonify({'success': True, 'message': '简历解析成功', 'parsed_content': parsed_resume})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main.route('/match', methods=['POST'])
def match_resume_to_jobs():
    """
    Process a request to match a resume against multiple job descriptions.

    :return: JSON response containing matching results or error information
    """
    data = request.get_json()
    resume = data.get('resume')
    job_descriptions = data.get('job_descriptions', [])

    print("Debug: Received resume data:")
    print(json.dumps(resume, indent=4, ensure_ascii=False))
    print("Debug: Received job descriptions:")
    print(json.dumps(job_descriptions, indent=4, ensure_ascii=False))

    if not resume or not isinstance(resume, dict):
        return jsonify({
            'success': False,
            'message': 'Invalid or missing resume data'
        }), 400

    if not job_descriptions or not isinstance(job_descriptions, list):
        return jsonify({
            'success': False,
            'message': 'Invalid or missing job description data'
        }), 400

    try:
        overall_results = {
            "overview": "This document provides a detailed analysis of the provided resume against multiple job descriptions. Each job is evaluated across four dimensions: Education, Work Experience, Skills, and Project Experience.",
            "job_results": []
        }

        for job in job_descriptions:
            jd_id = job.get('jd_id')  # 获取用户提供的jd_id
            if not jd_id:
                return jsonify({
                    'success': False,
                    'message': f'Missing jd_id for job: {job["title"]}'
                }), 400

            print(f"Debug: Processing job: {job['title']} with jd_id: {jd_id}")
            job_report = generate_job_match_report(resume, job, jd_id)  # 传递jd_id
            overall_results["job_results"].append(job_report)

        overall_results["job_results"].sort(key=lambda x: x["total_score"], reverse=True)

        return jsonify({
            'success': True,
            'results': overall_results
        })

    except Exception as e:
        print(f"Unhandled exception in /match route: {e}")
        print(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            'success': False,
            'error': 'An internal server error occurred',
            'message': str(e)
        }), 500


@main.route('/parse_jd', methods=['POST'])
def parse_jd():
    """
    接收用户输入的JD内容，使用GPT-4模型解析并返回JSON格式
    """
    data = request.get_json()
    jd_content = data.get('jd_content')

    if not jd_content:
        return jsonify({'success': False, 'message': 'JD内容为空'}), 400

    try:
        # 调用GPT-4接口，将JD内容解析为JSON
        parsed_jd = gpt4_parse_jd_to_json(jd_content,client)

        if parsed_jd is None:
            return jsonify({'success': False, 'message': 'JD解析失败'}), 500

        return jsonify({'success': True, 'message': 'JD解析成功', 'parsed_jd': parsed_jd})

    except Exception as e:
        print(f"Exception occurred while parsing JD: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
