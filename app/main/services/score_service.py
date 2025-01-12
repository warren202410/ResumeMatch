import json
from typing import Dict, Tuple

from app.utils.helpers import gpt4_analyze, calculate_duration, parse_gpt4_response, parse_gpt4_response_extended


import json
from typing import Dict, Tuple

def calculate_education_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    """
    Calculate the education score

    :param resume: Candidate's resume
    :param job: Job description
    :return: Education score (0-100) and explanation
    """
    resume_degree = resume['education'][0]['degree']
    prompt = f"""
    Given the following job description and candidate's education:

    Job: {job['title']}
    Required Qualifications: {job.get('requiredQualifications', 'Not specified')}

    Candidate's Education: {resume_degree}

    Score the education match on a scale of 0-4:
    0 - No relevant degree
    1 - Bachelor's in unrelated field
    2 - Bachelor's in related field
    3 - Master's in related field
    4 - PhD in related field

    Provide the score and a brief explanation in the following format:
    Score: [Your score]
    Explanation: [Your explanation]
    """

    response = gpt4_analyze(prompt)

    # More flexible response parsing
    lines = response.split('\n')
    score = None
    explanation = []
    for line in lines:
        if line.startswith("Score:"):
            try:
                score = float(line.split(':')[1].strip())
            except ValueError:
                print(f"Warning: Unable to parse score from the following line: {line}")
        elif line.startswith("Explanation:"):
            explanation = [line.split(':', 1)[1].strip()]
        elif score is not None:
            explanation.append(line.strip())

    if score is None:
        print(f"Warning: No score found in GPT-4 response. Using default score of 2.")
        score = 2

    # Normalize the 0-4 score to 0-100
    normalized_score = (score / 4) * 100
    explanation_text = ' '.join(explanation)
    return normalized_score, f"Education score: {normalized_score:.2f}%. {explanation_text}"


def calculate_experience_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    """
    Calculate the work experience score

    :param resume: Candidate's resume
    :param job: Job description
    :return: Experience score (0-100) and explanation
    """
    # Calculate the candidate's total years of experience
    candidate_years = sum(calculate_duration(exp['duration']) for exp in resume.get('experience', []))

    # Check the structure of education information
    education = resume.get('education', [])
    if isinstance(education, list):
        # If it's a list, find the highest degree
        degrees = [edu.get('degree', '').lower() for edu in education]
        has_masters = any('master' in degree for degree in degrees)
    elif isinstance(education, dict):
        # If it's a dictionary, directly check the degree
        has_masters = 'master' in education.get('degree', '').lower()
    else:
        print(f"Warning: Unexpected education information format: {type(education)}")
        has_masters = False

    # If the candidate has a master's degree, add 1.5 years of experience
    if has_masters:
        candidate_years += 1.5  # Average between 1-2 years

    job_required_years = job.get('requiredYearsOfExperience')

    prompt = f"""
    Given the following job description and candidate's experience:

    Job: {job['title']}
    Required Years of Experience: {job_required_years if job_required_years is not None else 'Not specified'}
    Required Qualifications: {job.get('requiredQualifications', 'Not specified')}

    Candidate's Years of Experience: {candidate_years:.2f}

    Score the experience match on a scale of 0-3:
    0 - Less than required
    1 - Meets minimum requirement
    2 - Exceeds requirement by 1-2 years
    3 - Exceeds requirement by more than 2 years

    Note: If the job doesn't specify required years of experience, assume the candidate's experience is a match (score 2).

    Provide the score and a brief explanation in the following format:
    Score: [Your score]
    Explanation: [Your explanation]
    """

    response = gpt4_analyze(prompt)
    score, explanation = parse_gpt4_response(response, (0, 3))
    # Normalize the 0-3 score to 0-100
    normalized_score = (score / 3) * 100
    return normalized_score, f"Work experience score: {normalized_score:.2f}%. {explanation}"


def calculate_skills_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    """
    Calculate the skills match score

    :param resume: Candidate's resume
    :param job: Job description
    :return: Skills score (0-100) and explanation
    """
    prompt = f"""
    Given the following job requirements and candidate's skills:

    Job: {job['title']}
    Required Skills: {job.get('keySkills', 'Not specified')}

    Candidate's Skills: {', '.join(resume['skills'])}

    Evaluate the match between the required skills and the candidate's skills.
    Provide a percentage score (0-100) and a brief explanation in the following format:
    Score: [Your score]
    Explanation: [Your explanation]
    """

    response = gpt4_analyze(prompt)
    score, explanation = parse_gpt4_response(response)
    return score, f"Skills match score: {score:.2f}%. {explanation}"


def calculate_project_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    """
    Calculate the project experience match score

    :param resume: Candidate's resume
    :param job: Job description
    :return: Project experience score (0-100), brief explanation
    """
    prompt = f"""
    Given the following job responsibilities and candidate's project experience:

    Job: {job['title']}
    Job Responsibilities: {job.get('responsibilities', 'Not specified')}

    Candidate's Project Experience:
    {json.dumps(resume['experience'], indent=2)}

    Evaluate how well the candidate's project experience matches the job responsibilities.
    Provide a percentage score (0-100) and a brief explanation in the following format:
    Score: [Your score]
    Explanation: [Your brief explanation]
    """

    response = gpt4_analyze(prompt)
    print(f"Debug: GPT-4 returned response:\n{response}")

    score, explanation = parse_gpt4_response(response)
    return score, f"Project experience match score: {score:.2f}%. {explanation}"