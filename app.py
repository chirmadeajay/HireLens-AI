
import os
import json
import re
from io import BytesIO

import pandas as pd
import streamlit as st

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None

try:
    from groq import Groq
except Exception:
    Groq = None


APP_TITLE = "HireLens AI - Resume to JD Screening Assistant"


def clean_text(text: str) -> str:
    text = text or ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_uploaded_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        if PyPDF2 is None:
            return "PDF reading dependency is missing. Please install PyPDF2."
        reader = PyPDF2.PdfReader(BytesIO(raw))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    if name.endswith(".docx"):
        if docx is None:
            return "DOCX reading dependency is missing. Please install python-docx."
        document = docx.Document(BytesIO(raw))
        return "\n".join([p.text for p in document.paragraphs])

    return raw.decode("utf-8", errors="ignore")


def extract_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def fallback_score_resume(jd: str, resume: str, filename: str) -> dict:
    jd_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", jd.lower()))
    resume_words = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+.#-]{2,}", resume.lower()))

    useful_stopwords = {
        "the", "and", "with", "for", "from", "this", "that", "are", "you", "your",
        "have", "has", "will", "can", "our", "their", "into", "using", "work"
    }
    jd_words = {w for w in jd_words if w not in useful_stopwords}
    overlap = sorted(jd_words.intersection(resume_words))
    missing = sorted(jd_words.difference(resume_words))

    score = min(95, int((len(overlap) / max(len(jd_words), 1)) * 100) + 10)
    top_matches = overlap[:12]
    top_gaps = missing[:12]

    return {
        "candidate_name": filename.rsplit(".", 1)[0].replace("_", " ").title(),
        "fit_score": score,
        "decision": "Strong Match" if score >= 75 else "Possible Match" if score >= 55 else "Weak Match",
        "why_good_fit": top_matches[:6],
        "missing_or_weak_areas": top_gaps[:6],
        "recommended_role_fit": "Needs recruiter review",
        "interview_questions": [
            f"Can you explain your hands-on experience with {skill}?" for skill in top_matches[:5]
        ] or [
            "Can you walk through your most relevant project for this role?",
            "Which part of the job description matches your strongest experience?"
        ],
        "recruiter_summary": f"{filename} matches {len(overlap)} important JD terms. Key matches include: {', '.join(top_matches[:8])}.",
        "risk_flags": top_gaps[:4],
    }


def call_groq(jd: str, resume: str, filename: str, api_key: str, model: str) -> dict:
    if Groq is None:
        raise RuntimeError("Groq package is not installed.")

    client = Groq(api_key=api_key)
    prompt = f"""
You are an expert technical recruiter and hiring analyst.

Task:
Compare this candidate resume with the job description and return only valid JSON.

Scoring guidance:
- 90-100: excellent match, most required skills proven
- 75-89: strong match, minor gaps
- 55-74: possible match, several gaps
- 0-54: weak match

Return this exact JSON schema:
{{
  "candidate_name": "string",
  "fit_score": number,
  "decision": "Strong Match | Possible Match | Weak Match",
  "why_good_fit": ["bullet", "bullet", "bullet"],
  "missing_or_weak_areas": ["bullet", "bullet", "bullet"],
  "recommended_role_fit": "string",
  "interview_questions": ["question", "question", "question", "question", "question"],
  "recruiter_summary": "4-6 sentence summary",
  "risk_flags": ["risk", "risk"]
}}

Job Description:
{jd[:12000]}

Resume File Name:
{filename}

Resume:
{resume[:12000]}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return strict JSON only. Do not include markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1400,
    )
    content = response.choices[0].message.content
    parsed = extract_json(content)
    if not parsed:
        raise RuntimeError("AI response was not valid JSON.")
    return parsed


def make_markdown_report(results: list, jd_text: str) -> str:
    sorted_results = sorted(results, key=lambda x: x.get("fit_score", 0), reverse=True)
    lines = []
    lines.append("# HireLens AI Screening Report")
    lines.append("")
    lines.append("## Job Description Snapshot")
    lines.append(clean_text(jd_text)[:1200] + ("..." if len(jd_text) > 1200 else ""))
    lines.append("")
    lines.append("## Ranked Candidates")
    lines.append("")
    for idx, item in enumerate(sorted_results, start=1):
        lines.append(f"### {idx}. {item.get('candidate_name', 'Candidate')} - {item.get('fit_score', 0)}/100")
        lines.append(f"**Decision:** {item.get('decision', 'N/A')}")
        lines.append("")
        lines.append("**Recruiter Summary**")
        lines.append(item.get("recruiter_summary", ""))
        lines.append("")
        lines.append("**Why good fit**")
        for point in item.get("why_good_fit", []):
            lines.append(f"- {point}")
        lines.append("")
        lines.append("**Missing or weak areas**")
        for point in item.get("missing_or_weak_areas", []):
            lines.append(f"- {point}")
        lines.append("")
        lines.append("**Interview questions**")
        for q in item.get("interview_questions", []):
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines)


st.set_page_config(page_title=APP_TITLE, page_icon="🧠", layout="wide")

st.title("🧠 HireLens AI")
st.subheader("Resume-to-JD screening, ranking, gap analysis, and interview kit generator")

with st.sidebar:
    st.header("Free AI Setup")
    st.write("Use a free Groq API key for AI analysis. Without a key, the app still runs using a basic keyword fallback.")
    api_key = st.text_input("GROQ_API_KEY", type="password", value=os.getenv("GROQ_API_KEY", ""))
    model = st.selectbox(
        "Model",
        ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
        index=0
    )
    st.divider()
    st.write("Best demo flow:")
    st.write("1. Paste JD")
    st.write("2. Upload 2-5 resumes")
    st.write("3. Click Analyze")
    st.write("4. Download report")

st.markdown(
    """
    **Problem solved:** recruiters and hiring managers spend hours manually comparing resumes with a job description.
    HireLens AI turns that workflow into a few minutes by reading unstructured resumes and producing structured hiring insights.
    """
)

jd_text = st.text_area("Paste Job Description", height=220, placeholder="Paste the full job description here...")

uploaded_resumes = st.file_uploader(
    "Upload resumes",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

analyze = st.button("Analyze Candidates", type="primary", use_container_width=True)

if analyze:
    if not jd_text.strip():
        st.error("Please paste a job description first.")
        st.stop()

    if not uploaded_resumes:
        st.error("Please upload at least one resume.")
        st.stop()

    results = []
    progress = st.progress(0)

    for idx, file in enumerate(uploaded_resumes):
        resume_text = read_uploaded_file(file)
        resume_text = clean_text(resume_text)

        with st.spinner(f"Analyzing {file.name}..."):
            try:
                if api_key.strip():
                    result = call_groq(jd_text, resume_text, file.name, api_key.strip(), model)
                else:
                    result = fallback_score_resume(jd_text, resume_text, file.name)
            except Exception as e:
                st.warning(f"AI analysis failed for {file.name}. Using fallback scoring. Reason: {e}")
                result = fallback_score_resume(jd_text, resume_text, file.name)

            result["source_file"] = file.name
            results.append(result)

        progress.progress((idx + 1) / len(uploaded_resumes))

    results = sorted(results, key=lambda x: x.get("fit_score", 0), reverse=True)

    st.success("Analysis complete.")

    df = pd.DataFrame([
        {
            "Rank": i + 1,
            "Candidate": r.get("candidate_name", "Candidate"),
            "Score": r.get("fit_score", 0),
            "Decision": r.get("decision", "N/A"),
            "Recommended Fit": r.get("recommended_role_fit", "N/A"),
            "Source File": r.get("source_file", ""),
        }
        for i, r in enumerate(results)
    ])

    st.header("Ranked Shortlist")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Shortlist CSV", data=csv, file_name="hirelens_shortlist.csv", mime="text/csv")

    report = make_markdown_report(results, jd_text)
    st.download_button(
        "Download Full Screening Report",
        data=report.encode("utf-8"),
        file_name="hirelens_screening_report.md",
        mime="text/markdown",
    )

    st.header("Candidate Deep Dives")
    for r in results:
        with st.expander(f"{r.get('candidate_name', 'Candidate')} - {r.get('fit_score', 0)}/100 - {r.get('decision', '')}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Why good fit")
                for point in r.get("why_good_fit", []):
                    st.write(f"- {point}")

                st.subheader("Missing / weak areas")
                for point in r.get("missing_or_weak_areas", []):
                    st.write(f"- {point}")

            with col2:
                st.subheader("Interview questions")
                for q in r.get("interview_questions", []):
                    st.write(f"- {q}")

                st.subheader("Risk flags")
                for risk in r.get("risk_flags", []):
                    st.write(f"- {risk}")

            st.subheader("Recruiter summary")
            st.write(r.get("recruiter_summary", ""))
else:
    st.info("Paste a JD and upload resumes to begin.")

st.divider()
st.caption("Built for the Weekly AI Generalist Hackathon. Free deployment target: Streamlit Community Cloud + Groq API free/developer access.")
