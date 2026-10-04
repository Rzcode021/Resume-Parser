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
# RESUME PYDANTIC MODEL
# ==================================

class Resume(BaseModel):

    name: str

    email: str

    phone: str

    total_experience_years: float

    skills: list[str]

    experiences: list[str]

    education: list[str]

    projects: list[str]

    certifications: list[str]


# ==================================
# PARSE RESUME USING LLM
# ==================================

def parse_resume(resume_text):

    schema = Resume.model_json_schema()


    system_prompt = f"""
You are an AI Resume Parser.

Extract candidate information from the resume according
to the provided JSON schema.

Schema:

{schema}

Rules:

- Extract only information available in the resume.
- Do not invent information.
- total_experience_years should include only professional
  work experience and internships.
- Do NOT count education duration.
- Do NOT count personal project duration.
- If no professional or internship experience is mentioned,
  return 0.
- If a string field is missing, return an empty string.
- If a list field is missing, return an empty list.
- Return only valid JSON.
"""


    messages = [

        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": f"""
Extract candidate information from this resume:

{resume_text}
"""
        }

    ]


    # ==================================
    # CALL LLM
    # ==================================

    response = client.chat.completions.create(

        model=model,

        messages=messages,

        response_format={
            "type": "json_object"
        },

        max_completion_tokens=1500
    )


    # ==================================
    # GET LLM RESPONSE
    # ==================================

    answer = response.choices[0].message.content


    # ==================================
    # JSON STRING → PYTHON DICTIONARY
    # ==================================

    data = json.loads(answer)


    # ==================================
    # PYDANTIC VALIDATION
    # ==================================

    resume = Resume(**data)


    return resume