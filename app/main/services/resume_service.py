import json
import logging

from openai import OpenAI


def create_prompt(file_type, input_text):
    prompt = f"""
    Below is the content of a {file_type} document:
    {input_text}

    Please extract the following information and return it in JSON format:
    {{
        "introduction": "Full name",
        "email": "Email address",
        "phone": "Phone number",
        "experience": [
            {{
                "company": "Company name",
                "role": "Job title",
                "duration": "Employment duration",
                "responsibilities": [
                    "Responsibility 1",
                    "Responsibility 2",
                    "Responsibility 3"
                ]
            }}
        ],
        "skills": [
            "Skill 1",
            "Skill 2",
            "Skill 3"
        ],
        "education": [
            {{
                "degree": "Degree",
                "institution": "Educational institution",
                "graduation_year": "Year of graduation"
            }},
            {{
                "degree": "Second Degree",
                "institution": "Second Educational institution",
                "graduation_year": "Year of second graduation"
            }}
        ]
    }}
    """
    return prompt


def clean_data(input_text, file_type, api_key):
    client = OpenAI(api_key=api_key)
    prompt = create_prompt(file_type, input_text)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3200
        )
        logging.debug(f"GPT Response: {response}")

        gpt_response = response.choices[0].message.content.strip()
        logging.debug(f"GPT Raw Content: {gpt_response}")

        json_start = gpt_response.find('{')
        json_end = gpt_response.rfind('}') + 1
        json_content = gpt_response[json_start:json_end]

        return json.loads(json_content)
    except (json.JSONDecodeError, IndexError) as e:
        logging.error(f"Failed to decode JSON response from GPT: {e}")
        return None
