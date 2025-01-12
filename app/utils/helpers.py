import json
import re
from datetime import datetime
from typing import Tuple, Dict

from openai import OpenAI

from app import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)


def gpt4_analyze(prompt: str) -> str:
    print(f"Debug: Sending prompt to GPT-4:\n{prompt}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AI assistant helping with job application analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    result = response.choices[0].message.content.strip()
    print(f"Debug: GPT-4 returned response:\n{result}")
    return result


def parse_gpt4_response(response: str, score_range: Tuple[float, float] = (0, 100)) -> Tuple[float, str]:
    # First, try to find a score in the format "Score: X"
    score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)

    if score_match:
        try:
            score = float(score_match.group(1))
        except ValueError:
            print(f"Warning: Could not parse score from matched string: {score_match.group(0)}")
            score = None
    else:
        # If no score is found, look for any number in the response
        number_match = re.search(r'\d+(?:\.\d+)?', response)
        if number_match:
            try:
                score = float(number_match.group(0))
                print(f"Warning: Used a number found in the response as score: {score}")
            except ValueError:
                print(f"Warning: Could not parse number found in response: {number_match.group(0)}")
                score = None
        else:
            score = None

    if score is None:
        print(f"Warning: Could not find any valid score in GPT-4 response. Using default score.")
        score = (score_range[0] + score_range[1]) / 2  # Use the middle of the score range as default
    else:
        # Ensure the score is within the specified range
        score = max(score_range[0], min(score, score_range[1]))

    # Extract explanation
    explanation_match = re.search(r'Explanation:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
    if explanation_match:
        explanation = explanation_match.group(1).strip()
    else:
        explanation = "No specific explanation provided. " + response.strip()

    return score, explanation


def calculate_duration(duration_str: str) -> float:
    print(f"Debug: Calculating duration for '{duration_str}'")

    # Handle cases where duration is just a single date (e.g., "Present")
    if ' - ' not in duration_str:
        if duration_str.lower() == 'present':
            return 0  # Assume current job started recently
        else:
            try:
                start_date = datetime.strptime(duration_str, "%m/%Y")
                end_date = datetime.now()
            except ValueError:
                print(f"Warning: Unable to parse date '{duration_str}'. Assuming 0 duration.")
                return 0
    else:
        start, end = duration_str.split(' - ')
        try:
            start_date = datetime.strptime(start, "%m/%Y")
            end_date = datetime.now() if end.lower() == 'present' else datetime.strptime(end, "%m/%Y")
        except ValueError:
            print(f"Warning: Unable to parse date range '{duration_str}'. Assuming 0 duration.")
            return 0

    duration = (end_date - start_date).days / 365.25
    print(f"Debug: Calculated duration: {duration:.2f} years")
    return duration


def parse_gpt4_response_extended(response: str, score_range: Tuple[float, float] = (0, 100)) -> Tuple[float, str, str]:
    score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', response, re.IGNORECASE)
    explanation_match = re.search(r'Explanation:\s*(.+?)(?=Detailed Analysis:|$)', response, re.IGNORECASE | re.DOTALL)
    detailed_analysis_match = re.search(r'Detailed Analysis:\s*(.+)$', response, re.IGNORECASE | re.DOTALL)

    if score_match:
        score = float(score_match.group(1))
        score = max(score_range[0], min(score, score_range[1]))
    else:
        print(f"警告：无法在GPT-4响应中找到有效的分数。使用默认分数。")
        score = (score_range[0] + score_range[1]) / 2

    explanation = explanation_match.group(1).strip() if explanation_match else "未提供解释。"
    detailed_analysis = detailed_analysis_match.group(1).strip() if detailed_analysis_match else "未提供详细分析。"

    return score, explanation, detailed_analysis


def clean_explanation(explanation: str) -> str:
    # Remove score prefix in English
    pattern = r'^(Education|Work experience|Skills match|Project experience match)? ?score:?\s*\d+(\.\d+)?%\.?\s*'

    explanation = re.sub(pattern, '', explanation, flags=re.IGNORECASE)

    # Remove special characters and escape sequences
    explanation = re.sub(r'[\n\r\t]', ' ', explanation)
    explanation = re.sub(r'\s+', ' ', explanation)

    return explanation.strip()


# In the main function or wherever you process the dimensions
def process_dimensions(dimensions: Dict) -> Dict:
    for key, value in dimensions.items():
        if 'explanation' in value:
            value['explanation'] = clean_explanation(value['explanation'])
    return dimensions


def gpt4_parse_jd_to_json(jd_content, client):
    """
    使用GPT-4解析JD内容为JSON格式
    :param jd_content: 职位描述文本
    :param api_key: GPT-4 API Key
    :return: 解析后的JSON格式数据
    """
    prompt = f"Please parse the following job description into a structured JSON format:\n\n{jd_content}\n\nThe output should include fields such as job title, responsibilities, requirements, skills, and experience."


    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant that specializes in parsing job descriptions "
                                              "into structured JSON formats."},
                {"role": "user", "content": prompt}
            ]
        )
        print("Debug: GPT-4 API Response:", response)
        parsed_jd = response.choices[0].message.content.strip()

        # 将解析后的结果转换为Python的字典格式
        # 去掉markdown的代码块标记 ```json 和 ```
        if parsed_jd.startswith("```json"):
            parsed_jd = parsed_jd[7:]  # 去掉 ```json
        if parsed_jd.endswith("```"):
            parsed_jd = parsed_jd[:-3]  # 去掉 ```

        # 打印解析文本以调试
        print("Debug: Cleaned JD Text:", parsed_jd)

        # 将解析后的文本转换为Python字典格式
        parsed_jd_json = json.loads(parsed_jd)
        return parsed_jd_json

    except json.JSONDecodeError as json_error:
        print(f"JSONDecodeError: {json_error}")
        print(f"Response text: {parsed_jd}")  # 打印返回的文本内容以帮助调试
        return None

    except Exception as e:
        print(f"Error parsing JD with GPT-4: {e}")
        return None
