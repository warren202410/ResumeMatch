import traceback
from typing import Dict

from app.main.services.score_service import calculate_education_score, calculate_skills_score, calculate_project_score, \
    calculate_experience_score
from app.utils.helpers import clean_explanation


def generate_job_match_report(resume: Dict, job: Dict, jd_id: str) -> Dict:
    """
    Generate a job match report

    :param resume: Candidate's resume (dictionary format)
    :param job: Job description (dictionary format)
    :param jd_id: The unique identifier for the job description
    :return: Dictionary containing detailed match report information
    """
    try:
        # Calculate scores and explanations for each aspect
        education_score, education_explanation = calculate_education_score(resume, job)
        experience_score, experience_explanation = calculate_experience_score(resume, job)
        skills_score, skills_explanation = calculate_skills_score(resume, job)
        project_score, project_explanation = calculate_project_score(resume, job)

        # Calculate total score, with weights as follows:
        # Education: 10%, Work Experience: 25%, Skills Match: 25%, Project Experience: 40%
        total_score = (
                education_score * 0.1 +
                experience_score * 0.25 +
                skills_score * 0.25 +
                project_score * 0.4
        )

        # Generate report
        report = {
            "jd_id": jd_id,  # 包含jd_id
            "job_title": job['title'],
            "total_score": round(total_score, 2),
            "dimensions": {
                "education": {
                    "score": round(education_score, 2),
                    "explanation": clean_explanation(education_explanation)
                },
                "experience": {
                    "score": round(experience_score, 2),
                    "explanation": clean_explanation(experience_explanation)
                },
                "skills": {
                    "score": round(skills_score, 2),
                    "explanation": clean_explanation(skills_explanation)
                },
                "project": {
                    "score": round(project_score, 2),
                    "explanation": clean_explanation(project_explanation)
                }
            },
            "summary": f"The candidate's resume matches {total_score:.2f}% with this position."
        }

        # Provide overall evaluation based on total score
        if total_score >= 80:
            report["summary"] += " The candidate is an excellent fit for this position."
        elif total_score >= 60:
            report["summary"] += " The candidate is suitable for this position but may need some additional training or experience."
        else:
            report["summary"] += " Based on current qualifications, the candidate may not be the best fit for this position."

        return report
    except Exception as e:
        print(f"Error generating job match report: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "jd_id": jd_id,  # 包含jd_id
            "error": f"Unable to generate report. Error: {str(e)}",
            "job_title": job.get('title', 'Unknown'),
            "total_score": 0
        }
