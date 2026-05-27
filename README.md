# HireLens AI - Resume to JD Screening Assistant

HireLens AI is a free-to-run AI recruiting assistant that compares resumes against a job description and generates a ranked shortlist, fit score, gap analysis, recruiter summary, and interview questions.

## Hackathon Problem

Recruiters, founders, and hiring managers often spend 2 to 5 hours manually reviewing resumes for one role. The work is repetitive but still requires judgment: matching skills, spotting gaps, and preparing interview questions.

HireLens AI reduces that workflow to a few minutes.

## Target Users

- Recruiters
- HR teams
- Startup founders
- Hiring managers
- Career consultants

## What the AI Does

The app reads unstructured resumes and a job description, then produces structured hiring output:

- Candidate fit score
- Strong Match / Possible Match / Weak Match decision
- Why the candidate fits
- Missing or weak areas
- Interview questions
- Recruiter summary
- Risk flags
- Downloadable shortlist CSV
- Downloadable screening report

## Free Tools Used

- Python
- Streamlit
- Groq API with `llama-3.1-8b-instant`
- Streamlit Community Cloud for free hosting
- PyPDF2 and python-docx for document reading

The app also includes a fallback keyword scoring mode, so it still runs even if no API key is added.

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Groq API Setup

1. Create a free Groq account.
2. Generate an API key.
3. Add it in the app sidebar or set it as an environment variable:

```bash
set GROQ_API_KEY=your_api_key_here
```

For Mac/Linux:

```bash
export GROQ_API_KEY=your_api_key_here
```

## Streamlit Cloud Deployment

1. Push these files to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app from the repo.
4. Main file path: `app.py`
5. Add your `GROQ_API_KEY` in Streamlit secrets.
6. Deploy.

## Demo Flow

1. Open the app.
2. Paste the sample job description from `sample_data/sample_job_description.txt`.
3. Upload the sample resumes from `sample_data`.
4. Click Analyze Candidates.
5. Show the ranked table.
6. Open candidate deep dives.
7. Download CSV and Markdown report.

## Why This Can Score Well

### Problem Framing
The problem is real, specific, and relevant to professionals. Resume screening consumes hours for recruiters and hiring teams.

### AI Leverage
AI reads unstructured resumes and converts them into structured hiring decisions, summaries, gaps, and interview questions.

### Practical Usefulness
The app saves time, reduces manual effort, and improves consistency in screening.

### Execution Quality
It works end-to-end with uploads, AI analysis, ranking, and downloadable outputs.

### Clarity
The workflow is simple: paste JD, upload resumes, analyze, download report.
