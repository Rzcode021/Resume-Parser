import os
import json

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

from job_parser import JobDescription
from resume_parser import Resume


# ==================================
# LOAD ENVIRONMENT VARIABLES
# ==================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing")


# ==================================
# CREATE GROQ CLIENT
# ==================================

client = Groq(api_key=api_key)

model = "qwen/qwen3.8-27b"


# ==================================
# MATCH RESULT MODEL
# ==================================

class MatchDetails(BaseModel):

    matching_skills: list[str]

    missing_skills: list[str]

    experience_requirement_met: bool

    verdict: str


class MatchResult(BaseModel):

    score: float

    details: MatchDetails


# ==================================
# MATCH CANDIDATE WITH JOB
# ==================================

def match_candidate(job, resume):

    schema = MatchResult.model_json_schema()


    system_prompt = f"""
You are an experienced HR recruiter.

Your task is to compare a candidate's resume with
a job description and evaluate how well the candidate
matches the role.

You must analyze:

1. Required skills
2. Preferred skills
3. Professional experience
4. Education requirements
5. Project relevance
6. Overall relevance to the job role

Generate a realistic overall match score from 0 to 100.

Scoring guidelines:

- 80 to 100:
  Excellent or strong match.

- 60 to 79:
  Good match with some missing requirements.

- 40 to 59:
  Moderate match.

- 0 to 39:
  Weak match.

Important rules:

- Do not invent skills or experience.
- Use only information present in the candidate data.
- Matching skills can include semantically related skills,
  not only exact keyword matches.
- Give more importance to required skills than preferred skills.
- Give a realistic score. Do not give everyone a high score.
- The verdict should be short and clear.

Return the result strictly according to this JSON schema:

{schema}

Return only valid JSON.
"""


    user_prompt = f"""
Compare the following job requirements and candidate.

JOB DESCRIPTION:

{job.model_dump_json(indent=2)}


CANDIDATE RESUME:

{resume.model_dump_json(indent=2)}
"""


    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": user_prompt
        }

    ]


    # ==================================
    # CALL LLM FOR MATCHING
    # ==================================

    response = client.chat.completions.create(

        model=model,

        messages=messages,

        response_format={
            "type": "json_object"
        },

        max_completion_tokens=1000
    )


    # ==================================
    # GET RESPONSE
    # ==================================

    answer = response.choices[0].message.content


    # ==================================
    # JSON STRING → DICTIONARY
    # ==================================

    data = json.loads(answer)


    # ==================================
    # VALIDATE USING PYDANTIC
    # ==================================

    result = MatchResult(**data)


    return result