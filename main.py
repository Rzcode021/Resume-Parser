import os
import json
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

from pypdf import PdfReader
from docx import Document


# ==================================
# LOAD ENVIRONMENT VARIABLES
# ==================================

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key missing")


# ==================================
# CREATE GROQ CLIENT
# ==================================

client = Groq(api_key=my_api_key)

model = "qwen/qwen3.8-27b"


# ==================================
# EXTRACT PDF TEXT
# ==================================

def extract_pdf_text(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ==================================
# EXTRACT DOCX TEXT
# ==================================

def extract_docx_text(file_path):

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        text += paragraph.text + "\n"

    return text


# ==================================
# DETECT FILE TYPE
# ==================================

def extract_resume_text(file_path):

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":

        return extract_pdf_text(file_path)

    elif extension == ".docx":

        return extract_docx_text(file_path)

    else:

        raise ValueError(
            "Unsupported file type. Please provide a PDF or DOCX file."
        )


# ==================================
# RESUME PYDANTIC MODEL
# ==================================

class Resume(BaseModel):

    name: str
    email: str
    phone: str

    skills: list[str]

    experience: list[str]
    experience_years: float

    projects: list[str]

    education: list[str]


# ==================================
# HR REQUIREMENTS MODEL
# ==================================

class HRRequirements(BaseModel):

    required_skills: list[str]

    minimum_experience_years: float

    required_project_keywords: list[str]


# ==================================
# GENERATE JSON SCHEMA
# ==================================

schema = Resume.model_json_schema()


# ==================================
# FORCE JSON OUTPUT
# ==================================

response_format = {
    "type": "json_object"
}


# ==================================
# READ RESUME FILE
# ==================================

file_path = "resumes/resume.pdf"

resume_text = extract_resume_text(file_path)


# ==================================
# PRINT EXTRACTED RESUME TEXT
# ==================================

print("\n" + "=" * 50)
print("EXTRACTED TEXT FROM RESUME")
print("=" * 50)

print(resume_text)


# ==================================
# SYSTEM PROMPT
# ==================================

system_prompt = f"""
You are an AI Resume Parser.

Extract candidate information from the resume strictly
according to the provided JSON schema.

For experience_years:

- Count only professional work experience or internships.
- Do NOT count education duration.
- Do NOT count personal projects.
- If no professional or internship experience is mentioned,
  return 0.

If information is not available:

- Use an empty string for missing string fields.
- Use an empty list for missing list fields.
- Use 0 for missing numeric fields.

Return only a valid JSON object.

Schema:

{schema}
"""


# ==================================
# SYSTEM MESSAGE
# ==================================

message_system = {
    "role": "system",
    "content": system_prompt
}


# ==================================
# USER PROMPT
# ==================================

prompt = f"""
This is a candidate's resume.

Extract the required information from this resume.

Resume:

{resume_text}
"""


# ==================================
# USER MESSAGE
# ==================================

message = {
    "role": "user",
    "content": prompt
}


# ==================================
# MESSAGES
# ==================================

messages = [
    message_system,
    message
]


# ==================================
# LLM CALL
# ==================================

response = client.chat.completions.create(

    model=model,

    messages=messages,

    response_format=response_format,

    max_completion_tokens=1000
)


# ==================================
# GET RAW JSON RESPONSE
# ==================================

answer = response.choices[0].message.content


print("\n" + "=" * 50)
print("RAW JSON FROM LLM")
print("=" * 50)

print(answer)


# ==================================
# CONVERT JSON STRING TO DICTIONARY
# ==================================

data_file = json.loads(answer)


# ==================================
# VALIDATE USING PYDANTIC
# ==================================

resume = Resume(**data_file)


# ==================================
# PRINT PARSED RESUME JSON
# ==================================

print("\n" + "=" * 50)
print("PARSED RESUME JSON")
print("=" * 50)

print(resume.model_dump_json(indent=4))


# ==================================
# VERSION 3 - HR REQUIREMENTS
# ==================================

hr = HRRequirements(

    required_skills=[
        "Python",
        "Node.js",
        "MongoDB",
        "Machine Learning",
        "FastAPI"
    ],

    minimum_experience_years=0,

    required_project_keywords=[
        "AI",
        "Machine Learning",
        "Web"
    ]
)


# ==================================
# SKILL MATCHING FUNCTION
# ==================================

def calculate_skill_match(candidate_skills, required_skills):

    # Convert candidate skills to lowercase
    candidate_skills_lower = [

        skill.lower()

        for skill in candidate_skills
    ]

    matched_skills = []


    # Check each required skill
    for skill in required_skills:

        if skill.lower() in candidate_skills_lower:

            matched_skills.append(skill)


    # Avoid division by zero
    if len(required_skills) == 0:

        return 100, []


    # Calculate percentage
    match_percentage = (

        len(matched_skills)

        /

        len(required_skills)

    ) * 100


    return match_percentage, matched_skills


# ==================================
# EXPERIENCE MATCHING FUNCTION
# ==================================

def calculate_experience_match(

    candidate_experience,

    required_experience

):

    # Avoid division by zero
    if required_experience == 0:

        return 100


    percentage = (

        candidate_experience

        /

        required_experience

    ) * 100


    # Maximum percentage should be 100
    return min(percentage, 100)


# ==================================
# PROJECT MATCHING FUNCTION
# ==================================

def calculate_project_match(

    candidate_projects,

    required_keywords

):

    # Combine all project names
    all_projects = " ".join(

        candidate_projects

    ).lower()


    matched_keywords = []


    # Check each required keyword
    for keyword in required_keywords:

        if keyword.lower() in all_projects:

            matched_keywords.append(keyword)


    # Avoid division by zero
    if len(required_keywords) == 0:

        return 100, []


    # Calculate percentage
    match_percentage = (

        len(matched_keywords)

        /

        len(required_keywords)

    ) * 100


    return match_percentage, matched_keywords


# ==================================
# PERFORM SKILL MATCHING
# ==================================

skill_percentage, matched_skills = calculate_skill_match(

    resume.skills,

    hr.required_skills
)


# ==================================
# PERFORM EXPERIENCE MATCHING
# ==================================

experience_percentage = calculate_experience_match(

    resume.experience_years,

    hr.minimum_experience_years
)


# ==================================
# PERFORM PROJECT MATCHING
# ==================================

project_percentage, matched_project_keywords = (

    calculate_project_match(

        resume.projects,

        hr.required_project_keywords
    )
)


# ==================================
# CALCULATE OVERALL MATCH SCORE
# ==================================

overall_match = (

    skill_percentage * 0.50

    +

    experience_percentage * 0.30

    +

    project_percentage * 0.20
)


# ==================================
# CANDIDATE RECOMMENDATION
# ==================================

if overall_match >= 75:

    recommendation = "Strong Match"

elif overall_match >= 50:

    recommendation = "Moderate Match"

else:

    recommendation = "Weak Match"


# ==================================
# PRINT SKILL MATCH RESULT
# ==================================

print("\n" + "=" * 50)
print("SKILL MATCH RESULT")
print("=" * 50)


print("\nHR Required Skills:")

for skill in hr.required_skills:

    print("-", skill)


print("\nCandidate Skills:")

for skill in resume.skills:

    print("-", skill)


print("\nMatched Skills:")

for skill in matched_skills:

    print("-", skill)


print(

    f"\nSkill Match Percentage: "

    f"{skill_percentage:.2f}%"
)


# ==================================
# PRINT EXPERIENCE MATCH RESULT
# ==================================

print("\n" + "=" * 50)
print("EXPERIENCE MATCH RESULT")
print("=" * 50)


print(

    f"\nCandidate Experience: "

    f"{resume.experience_years} years"
)


print(

    f"Required Experience: "

    f"{hr.minimum_experience_years} years"
)


print(

    f"\nExperience Match Percentage: "

    f"{experience_percentage:.2f}%"
)


# ==================================
# PRINT PROJECT MATCH RESULT
# ==================================

print("\n" + "=" * 50)
print("PROJECT MATCH RESULT")
print("=" * 50)


print("\nHR Required Project Keywords:")

for keyword in hr.required_project_keywords:

    print("-", keyword)


print("\nCandidate Projects:")

for project in resume.projects:

    print("-", project)


print("\nMatched Project Keywords:")

for keyword in matched_project_keywords:

    print("-", keyword)


print(

    f"\nProject Match Percentage: "

    f"{project_percentage:.2f}%"
)


# ==================================
# PRINT FINAL RESULT
# ==================================

print("\n" + "=" * 50)
print("FINAL CANDIDATE MATCH RESULT")
print("=" * 50)


print(

    f"\nCandidate Name: "

    f"{resume.name}"
)


print(

    f"\nSkills Match: "

    f"{skill_percentage:.2f}%"
)


print(

    f"Experience Match: "

    f"{experience_percentage:.2f}%"
)


print(

    f"Project Match: "

    f"{project_percentage:.2f}%"
)


print("\n" + "-" * 50)


print(

    f"\nOVERALL MATCH SCORE: "

    f"{overall_match:.2f}%"
)


print(

    f"\nRECOMMENDATION: "

    f"{recommendation}"
)


print("\n" + "=" * 50)