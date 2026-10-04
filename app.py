import streamlit as st

from file_reader import read_resume
from job_parser import parse_job_description
from resume_parser import parse_resume
from matcher import match_candidate


# ==================================
# PAGE CONFIGURATION
# ==================================

st.set_page_config(
    page_title="TalentAI - Resume Screening",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================
# SIDEBAR
# ==================================

with st.sidebar:

    st.title("🤖 TalentAI")

    st.write("### AI Resume Screening")

    st.divider()

    st.write(
        """
        **How it works:**

        1. Add Job Description
        2. Upload Candidate Resumes
        3. AI extracts information
        4. AI evaluates candidates
        5. Candidates are ranked
        """
    )

    st.divider()


    # ==================================
    # PRIVACY / DEMO MODE
    # ==================================

    demo_mode = st.toggle(
        "🔒 Privacy Demo Mode",
        value=True,
        help="Hide personal information for public demonstrations and screen recordings."
    )

    if demo_mode:

        st.success(
            "Privacy Mode ON"
        )

        st.caption(
            "Email, phone numbers, and raw resume data are hidden."
        )

    else:

        st.warning(
            "Privacy Mode OFF"
        )

        st.caption(
            "Personal candidate information may be visible."
        )


    st.divider()

    st.caption(
        "Powered by LLM + Pydantic + Streamlit"
    )


# ==================================
# HEADER
# ==================================

st.title("🎯 AI Resume Screening System")

st.subheader(
    "Screen, analyze, and rank candidates using Artificial Intelligence."
)

st.divider()


# ==================================
# INPUT SECTION
# ==================================

st.header("📋 Candidate Screening Setup")

col1, col2 = st.columns(2)


# ==================================
# JOB DESCRIPTION COLUMN
# ==================================

with col1:

    st.subheader("💼 Job Description")

    job_description = st.text_area(
        "Paste the job description",
        height=350,
        placeholder="""
Example:

We are looking for a Junior AI Engineer.

Required Skills:
- Python
- Machine Learning
- APIs
- SQL
- Git

Preferred Skills:
- LangChain
- RAG
- Vector Databases
        """
    )


# ==================================
# RESUME UPLOAD COLUMN
# ==================================

with col2:

    st.subheader("📄 Candidate Resumes")

    uploaded_files = st.file_uploader(
        "Upload PDF or DOCX resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if uploaded_files:

        st.success(
            f"{len(uploaded_files)} candidate(s) uploaded"
        )

        st.write("### Uploaded Files")

        for file in uploaded_files:

            st.write(
                f"📄 {file.name}"
            )

    else:

        st.info(
            "Upload one or multiple candidate resumes."
        )


st.divider()


# ==================================
# ANALYZE BUTTON
# ==================================

analyze_button = st.button(
    "🚀 Analyze Candidates",
    type="primary",
    use_container_width=True
)


# ==================================
# ANALYSIS
# ==================================

if analyze_button:

    # ==================================
    # VALIDATION
    # ==================================

    if not job_description.strip():

        st.error(
            "⚠️ Please enter a job description."
        )

    elif not uploaded_files:

        st.error(
            "⚠️ Please upload at least one resume."
        )

    else:

        # ==================================
        # PARSE JOB DESCRIPTION
        # ==================================

        with st.status(
            "🤖 AI is analyzing the job description...",
            expanded=True
        ) as status:

            st.write(
                "Extracting required skills..."
            )

            parsed_job = parse_job_description(
                job_description
            )

            st.write(
                "Job requirements structured successfully."
            )

            status.update(
                label="Job Description Analyzed",
                state="complete",
                expanded=False
            )


        # ==================================
        # SHOW JOB REQUIREMENTS
        # ==================================

        with st.expander(
            "📋 View Extracted Job Requirements"
        ):

            st.json(
                parsed_job.model_dump()
            )


        st.divider()


        # ==================================
        # PROCESS CANDIDATES
        # ==================================

        st.header(
            "🤖 AI Candidate Analysis"
        )

        all_results = []

        progress_bar = st.progress(0)

        total_candidates = len(uploaded_files)


        # ==================================
        # PROCESS EACH RESUME
        # ==================================

        for index, file in enumerate(
            uploaded_files,
            start=1
        ):

            progress_value = index / total_candidates

            progress_bar.progress(
                progress_value,
                text=(
                    f"Processing candidate "
                    f"{index}/{total_candidates}: "
                    f"{file.name}"
                )
            )


            # ==================================
            # PROCESS RESUME
            # ==================================

            with st.status(
                f"📄 Processing {file.name}",
                expanded=False
            ) as candidate_status:


                st.write(
                    "📄 Reading resume..."
                )

                resume_text = read_resume(
                    file
                )


                st.write(
                    "🤖 Extracting candidate information..."
                )

                parsed_resume = parse_resume(
                    resume_text
                )


                st.write(
                    "🎯 Matching candidate with job..."
                )

                match_result = match_candidate(
                    parsed_job,
                    parsed_resume
                )


                candidate_status.update(
                    label=(
                        f"✅ {parsed_resume.name} "
                        f"analyzed successfully"
                    ),
                    state="complete",
                    expanded=False
                )


            # ==================================
            # STORE RESULT
            # ==================================

            candidate_result = {

                "name": parsed_resume.name,

                "email": parsed_resume.email,

                "phone": parsed_resume.phone,

                "score": match_result.score,

                "matching_skills":
                    match_result.details.matching_skills,

                "missing_skills":
                    match_result.details.missing_skills,

                "experience_requirement_met":
                    match_result.details.experience_requirement_met,

                "verdict":
                    match_result.details.verdict,

                "resume_data":
                    parsed_resume.model_dump()
            }


            all_results.append(
                candidate_result
            )


        # ==================================
        # COMPLETE PROGRESS
        # ==================================

        progress_bar.empty()


        # ==================================
        # SORT CANDIDATES BY SCORE
        # ==================================

        all_results.sort(
            key=lambda candidate: candidate["score"],
            reverse=True
        )


        # ==================================
        # DASHBOARD METRICS
        # ==================================

        st.divider()

        st.header(
            "📊 Candidate Dashboard"
        )


        total_candidates = len(
            all_results
        )

        top_score = max(
            candidate["score"]
            for candidate in all_results
        )

        average_score = sum(
            candidate["score"]
            for candidate in all_results
        ) / total_candidates

        strong_candidates = sum(
            1
            for candidate in all_results
            if candidate["score"] >= 70
        )


        # ==================================
        # DISPLAY METRICS
        # ==================================

        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "👥 Total Candidates",
                total_candidates
            )


        with col2:

            st.metric(
                "🏆 Top Score",
                f"{top_score:.1f}%"
            )


        with col3:

            st.metric(
                "📈 Average Score",
                f"{average_score:.1f}%"
            )


        with col4:

            st.metric(
                "⭐ Strong Matches",
                strong_candidates
            )


        st.divider()


        # ==================================
        # FINAL RANKING
        # ==================================

        st.header(
            "🏆 Candidate Ranking"
        )


        tab_names = []

        for rank, candidate in enumerate(
            all_results,
            start=1
        ):

            tab_names.append(
                f"#{rank} {candidate['name']}"
            )


        tabs = st.tabs(
            tab_names
        )


        # ==================================
        # DISPLAY EACH CANDIDATE
        # ==================================

        for index, candidate in enumerate(
            all_results
        ):

            with tabs[index]:

                rank = index + 1


                # ==================================
                # CANDIDATE HEADER
                # ==================================

                st.subheader(
                    f"#{rank} — {candidate['name']}"
                )


                # ==================================
                # SCORE + VERDICT
                # ==================================

                score_col, verdict_col = st.columns(
                    2
                )


                with score_col:

                    st.metric(
                        "🎯 Match Score",
                        f"{candidate['score']:.1f}%"
                    )

                    st.progress(
                        min(
                            int(candidate["score"]),
                            100
                        )
                    )


                with verdict_col:

                    st.write(
                        "### 🤖 AI Verdict"
                    )

                    st.info(
                        candidate["verdict"]
                    )


                st.divider()


                # ==================================
                # CANDIDATE INFORMATION
                # ==================================

                st.write(
                    "### 👤 Candidate Information"
                )

                info_col1, info_col2 = st.columns(2)


                # ==================================
                # PRIVACY MODE
                # ==================================

                if demo_mode:

                    with info_col1:

                        st.write(
                            "📧 **Email:** Hidden for privacy"
                        )


                    with info_col2:

                        st.write(
                            "📱 **Phone:** Hidden for privacy"
                        )


                # ==================================
                # NORMAL HR MODE
                # ==================================

                else:

                    with info_col1:

                        st.write(
                            f"📧 **Email:** "
                            f"{candidate['email']}"
                        )


                    with info_col2:

                        st.write(
                            f"📱 **Phone:** "
                            f"{candidate['phone']}"
                        )


                # ==================================
                # SKILLS SECTION
                # ==================================

                skill_col1, skill_col2 = st.columns(
                    2
                )


                # ==================================
                # MATCHING SKILLS
                # ==================================

                with skill_col1:

                    st.write(
                        "### ✅ Matching Skills"
                    )

                    if candidate[
                        "matching_skills"
                    ]:

                        for skill in candidate[
                            "matching_skills"
                        ]:

                            st.success(
                                skill
                            )

                    else:

                        st.info(
                            "No matching skills found."
                        )


                # ==================================
                # MISSING SKILLS
                # ==================================

                with skill_col2:

                    st.write(
                        "### ❌ Missing Skills"
                    )

                    if candidate[
                        "missing_skills"
                    ]:

                        for skill in candidate[
                            "missing_skills"
                        ]:

                            st.warning(
                                skill
                            )

                    else:

                        st.success(
                            "No major skills missing."
                        )


                st.divider()


                # ==================================
                # EXPERIENCE
                # ==================================

                st.write(
                    "### 💼 Experience Requirement"
                )


                if candidate[
                    "experience_requirement_met"
                ]:

                    st.success(
                        "Experience requirement met"
                    )

                else:

                    st.warning(
                        "Experience requirement not met"
                    )


                # ==================================
                # RAW DATA
                # ==================================

                if not demo_mode:

                    with st.expander(
                        "🔍 View Parsed Resume Data"
                    ):

                        st.json(
                            candidate[
                                "resume_data"
                            ]
                        )


                else:

                    st.caption(
                        "🔒 Parsed resume data hidden in Privacy Demo Mode."
                    )


# ==================================
# FOOTER
# ==================================

st.divider()

st.caption(
    "🤖 TalentAI • AI Powered Resume Screening System"
)