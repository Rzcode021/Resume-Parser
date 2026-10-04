import os
import json

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel


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
# JOB DESCRIPTION MODEL
# ==================================

class JobDescription(BaseModel):

    role: str

    required_skills: list[str]

    preferred_skills: list[str]

    minimum_experience: float

    education_requirements: list[str]

    responsibilities: list[str]


# ==================================
# PARSE JOB DESCRIPTION
# ==================================

def parse_job_description(job_text):

    schema = JobDescription.model_json_schema()


    system_prompt = f"""
You are an AI Job Description Parser.

Extract job requirements from the given job description.

Return the information strictly according to this JSON schema:

{schema}

Rules:

- Extract only skills explicitly mentioned or clearly required.
- Separate required skills and preferred skills.
- Extract minimum years of experience.
- If the job accepts freshers and no minimum experience is required,
  return 0.
- Extract education requirements.
- Extract main job responsibilities.
- If any list information is missing, return an empty list.
- Return only valid JSON.
"""


    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": job_text
        }

    ]


    response = client.chat.completions.create(

        model=model,

        messages=messages,

        response_format={
            "type": "json_object"
        },

        max_completion_tokens=1000
    )


    answer = response.choices[0].message.content


    # Convert JSON string to Python dictionary
    data = json.loads(answer)


    # Validate using Pydantic
    job = JobDescription(**data)


    return job