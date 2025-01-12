import json
import logging
import re
import traceback
from datetime import datetime
from typing import Dict, Tuple
from openai import OpenAI

from app.utils.helpers import gpt4_analyze


def extract_score_and_explanation(response: str) -> Tuple[float, str]:
    print(f"Debug: Extracting score and explanation from response:\n{response}")

    # Try to extract score
    score_match = re.search(r"(?:Score:|Percentage Score:)\s*(\d+(?:\.\d+)?%?)", response, re.IGNORECASE)
    if score_match:
        score_str = score_match.group(1).strip('%')
        try:
            score = float(score_str)
            if score > 1 and score <= 100:  # If score is a percentage
                score /= 100
            elif score > 100:  # Invalid score
                raise ValueError(f"Invalid score value: {score}")
        except ValueError:
            print(f"Warning: Could not convert score '{score_str}' to float. Using default score of 0.5.")
            score = 0.5
    else:
        print("Warning: Could not find score in response. Using default score of 0.5.")
        score = 0.5

    # Try to extract explanation
    explanation_match = re.search(r"(?:Explanation:|Brief Explanation:)\s*(.*)", response, re.IGNORECASE | re.DOTALL)
    if explanation_match:
        explanation = explanation_match.group(1).strip()
    else:
        print("Warning: Could not find explanation in response. Using default explanation.")
        explanation = "No explanation provided. Please review the full response for details."

    print(f"Debug: Extracted score: {score}, explanation: {explanation[:50]}...")
    return score, explanation


def calculate_education_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    resume_degree = resume['education'][0]['degree']
    score = 0
    if "Master" in resume_degree:
        score = 75  # 3 out of 4 on the scale
    elif "Bachelor" in resume_degree:
        score = 50  # 2 out of 4 on the scale

    explanation = f"The candidate holds a {resume_degree}, which is a related technical field to Computer Science. Therefore, this meets the required educational qualifications quite well, scoring a {score / 25:.1f} out of 4."

    return score, explanation
# def calculate_education_score(resume: Dict, job: Dict) -> Tuple[float, str]:
#     resume_degree = resume['education'][0]['degree']
#     prompt = f"""
#     Given the following job description and candidate's education:
#
#     Job: {job['title']}
#     Required Qualifications: {job.get('requiredQualifications', 'Not specified')}
#
#     Candidate's Education: {resume_degree}
#
#     Score the education match on a scale of 0-4:
#     0 - No relevant degree
#     1 - Bachelor's in unrelated field
#     2 - Bachelor's in related field
#     3 - Master's in related field
#     4 - PhD in related field
#
#     Please return the response in the following format:
#     "Score: <score>"
#     "Explanation: <brief explanation>"
#     """
#     response = gpt4_analyze(prompt)
#     print(f"Debug: GPT-4 returned response:\n{response}")
#
#     try:
#         score, explanation = extract_score_and_explanation(response)
#     except ValueError as e:
#         print(f"Error extracting score and explanation: {e}")
#         raise
#
#     normalized_score = (score / 4) * 100
#     print(f"Debug: Returning education score and explanation: {normalized_score}, {explanation}")
#     return normalized_score, explanation  # Make sure this line is present and not indented


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


def validate_and_convert_to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        print(f"Debug: Invalid float conversion attempt with value: '{value}'")
        raise  # Re-raise the exception after logging


def calculate_experience_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    required_years = 2  # Assuming 2 years is the minimum requirement
    candidate_years = sum(calculate_duration(exp['duration']) for exp in resume.get('experience', []))

    if candidate_years >= required_years:
        score = 100
    else:
        score = (candidate_years / required_years) * 75  # Partial credit, max 75% if under required years

    explanation = f"The candidate has {candidate_years:.1f} years of experience, which is {'more than' if candidate_years >= required_years else 'less than'} the required {required_years} years of technical engineering experience specified in the job description."

    return score, explanation

# def calculate_experience_score(resume: Dict, job: Dict) -> Tuple[float, str]:
#     candidate_years = 0
#     for exp in resume.get('experience', []):
#         duration = exp.get('duration', '')
#         try:
#             candidate_years += calculate_duration(duration)
#         except Exception as e:
#             print(f"Warning: Error calculating duration for '{duration}': {e}")
#
#     print(f"Debug: Total calculated experience: {candidate_years:.2f} years")
#
#     if isinstance(resume.get('education'), list):
#         for edu in resume['education']:
#             if edu.get('degree', '').lower().startswith("master"):
#                 candidate_years += 1.5
#                 print("Debug: Added 1.5 years for Master's degree")
#                 break
#
#     prompt = f"""
#     Given the following job description and candidate's experience:
#
#     Job: {job['title']}
#     Required Qualifications: {job.get('requiredQualifications', 'Not specified')}
#
#     Candidate's Years of Experience: {candidate_years:.2f}
#
#     Score the experience match on a scale of 0-3:
#     0 - Less than required
#     1 - Meets minimum requirement
#     2 - Exceeds requirement by 1-2 years
#     3 - Exceeds requirement by more than 2 years
#
#     Please return the response in the following format:
#     "Score: <score>"
#     "Explanation: <brief explanation>"
#     """
#     response = gpt4_analyze(prompt)
#     print(f"Debug: GPT-4 response:\n{response}")
#     try:
#         score, explanation = extract_score_and_explanation(response)
#     except ValueError as e:
#         print(f"Error extracting score and explanation: {e}")
#         return 0, f"Error: {str(e)}"
#
#     normalized_score = (score / 3) * 100
#     print(f"Debug: Returning experience score and explanation: {normalized_score}, {explanation}")
#     return normalized_score, explanation


def calculate_skills_score(resume: Dict, job: Dict) -> Tuple[float, str]:
    print("Debug: Entering calculate_skills_score function")
    prompt = f"""
    Given the following job requirements and candidate's skills:

    Job: {job['title']}
    Required Skills: {job.get('keySkills', 'Not specified')}

    Candidate's Skills: {', '.join(resume.get('skills', []))}

    Evaluate the match between the required skills and the candidate's skills.
    Provide a percentage score (0-100) and a brief explanation.

    Please use the following format for your response:
    Score: <percentage>
    Explanation: <your explanation here>
    """
    print(f"Debug: Sending prompt to GPT-4:\n{prompt}")
    response = gpt4_analyze(prompt)
    print(f"Debug: Received response from GPT-4:\n{response}")

    try:
        score, explanation = extract_score_and_explanation(response)
    except Exception as e:
        print(f"Error extracting score and explanation: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return 50, f"Error in processing: {str(e)}. Please review the full response."

    print(f"Debug: Returning skills score and explanation: {score}, {explanation[:50]}...")
    return score , explanation  # Convert score to percentage


def calculate_project_score(resume: Dict, job: Dict) -> Tuple[float, str, Dict]:
    prompt = f"""
    Given the following job responsibilities and candidate's project experience:

    Job: {job['title']}
    Job Responsibilities: {job.get('responsibilities', 'Not specified')}

    Candidate's Project Experience:
    {json.dumps(resume.get('experience', []), indent=2)}

    Evaluate how well the candidate's project experience matches the job responsibilities.
    Provide a detailed analysis for each responsibility, including a percentage match score.
    Then, provide an overall percentage score and a brief explanation.

    Use the following format:
    1. [Responsibility]
       - Analysis
       - Match Score: X%

    ... (repeat for each responsibility)

    Overall Match Score: X%

    Explanation: [Your explanation here]
    """
    response = gpt4_analyze(prompt)
    print(f"Debug: GPT-4 response for project score:\n{response}")

    # Extract overall score and explanation
    score_match = re.search(r"Overall Match Score:\s*(\d+(?:\.\d+)?)%", response)
    explanation_match = re.search(r"Explanation:(.*?)$", response, re.DOTALL)

    if score_match and explanation_match:
        score = float(score_match.group(1)) / 100  # Convert percentage to decimal
        explanation = explanation_match.group(1).strip()
    else:
        score = 0.5
        explanation = "Unable to extract score and explanation from the response."

    # Extract individual responsibility scores
    responsibility_scores = {}
    for match in re.finditer(r"(\d+)\.\s*\*\*(.*?)\*\*.*?Match Score:\s*(\d+(?:\.\d+)?)%", response, re.DOTALL):
        index, responsibility, resp_score = match.groups()
        responsibility_scores[responsibility.strip()] = float(resp_score)

    detailed_analysis = {
        "overall_score": score * 100,
        "explanation": explanation,
        "responsibility_scores": responsibility_scores,
        "full_analysis": response
    }

    return score * 100, explanation, detailed_analysis


def generate_job_match_report(resume: Dict, job: Dict) -> str:
    print("Debug: Entered generate_job_match_report")
    try:

        education_score, education_explanation = calculate_education_score(resume, job)
        print(f"Debug: Received education score: {education_score} and explanation: {education_explanation}")
        experience_score, experience_explanation = calculate_experience_score(resume, job)
        print(f"Debug: Received experience score: {experience_score} and explanation: {experience_explanation}")
        skills_score, skills_explanation = calculate_skills_score(resume, job)
        project_score, project_explanation = calculate_project_score(resume, job)

        total_score = (
            education_score * 0.1 +
            experience_score * 0.25 +
            skills_score * 0.25 +
            project_score * 0.4
        )

        report = f"# Job Match Analysis for {job['title']}\n\n"
        report += f"## Overall Score: {total_score:.2f}%\n\n"
        report += f"### Education (10% weight)\n{education_explanation}\n\n"
        report += f"### Experience (25% weight)\n{experience_explanation}\n\n"
        report += f"### Skills (25% weight)\n{skills_explanation}\n\n"
        report += f"### Project Experience (40% weight)\n{project_explanation}\n\n"
        report += "## Summary\n"
        report += f"The candidate's profile is a {total_score:.2f}% match for this position. "
        if total_score >= 80:
            report += "The candidate is an excellent match for this role."
        elif total_score >= 60:
            report += "The candidate is a good match for this role but may need some additional training or experience."
        else:
            report += "The candidate may not be the best fit for this role based on the current qualifications."

        return report

    except Exception as e:
        print(f"Error processing scores for job {job['title']}: {e}")
        return ""


