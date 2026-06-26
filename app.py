import os
import sys
import datetime
import subprocess
from dotenv import load_dotenv
from anthropic import Anthropic
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from core.parser import load_base_resume
from core.analyzer import generate_tailored_resume_content

load_dotenv()

TOKEN_FILE = "token.json"
SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID")
DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

google_scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_user_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = UserCredentials.from_authorized_user_file(TOKEN_FILE, google_scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Missing 'credentials.json' in root directory.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", google_scopes)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def build_latex_template(base: dict, ai_data: dict) -> str:
    exp_b = ai_data.get("optimized_experience_bullets", [])
    proj_b = ai_data.get("optimized_project_bullets", [])

    cleaned_exp = [str(item) for item in exp_b]
    cleaned_proj = [str(item) for item in proj_b]

    while len(cleaned_exp) < 7: cleaned_exp.append("Optimized system components using standard engineering methodologies.")
    while len(cleaned_proj) < 9: cleaned_proj.append("Engineered core features and structured test automation architectures.")

    def sanitize_for_latex(text: str) -> str:
        text = text.replace("\\&", "__AMP__").replace("&", "\\&").replace("__AMP__", "\\&")
        text = text.replace("\\%", "__PCT__").replace("%", "\\%").replace("__PCT__", "\\%")
        text = text.replace("\\_", "__UND__").replace("_", "\\_").replace("__UND__", "\\_")
        text = text.replace("—", "-").replace("–", "-")
        return text

    exp_b = [sanitize_for_latex(b) for b in cleaned_exp]
    proj_b = [sanitize_for_latex(b) for b in cleaned_proj]

    # Premium layout structure supporting strict 1-page bounds, clickable links, and italicized details
    template = r"""\documentclass[letterpaper,10pt]{article}
\usepackage{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{marvosym}
\usepackage{fontawesome5}

% Strict margin metrics to ensure zero-spill single page builds
\geometry{letterpaper, margin=0.35in, top=0.35in, bottom=0.35in}
\pagestyle{empty}

\setlist[itemize]{leftmargin=*, noitemsep, topsep=1pt, parsep=0pt, partopsep=0pt}

\begin{document}
\begin{center}
    {\Huge \textbf{Krissh Patel}} \\ \vspace{4pt}
    \small 
    \href{mailto:krisshpatel37@gmail.com}{\raisebox{-0.1ex}{\Letter}\ krisshpatel37@gmail.com} \ | \ 
    \href{https://linkedin.com/in/krissh-patel}{\raisebox{-0.1ex}{\faLinkedin}\ linkedin.com/in/krissh-patel} \ | \ 
    \href{https://github.com/imkrisshpatel}{\raisebox{-0.1ex}{\faGithub}\ github.com/imkrisshpatel}
\end{center}

\vspace{-4pt}
\noindent{\large \textbf{Education}} \\
\vspace{-9pt}
\hrule
\vspace{4pt}
\noindent \textbf{Toronto Metropolitan University} \hfill Toronto, ON \\
\noindent \textit{Master of Engineering (M.Eng.), Electrical and Computer Engineering} \hfill Sep 2026 - Present \\
\noindent \textit{Concentration: Artificial Intelligence}

\vspace{4pt}
\noindent \textbf{University of Western Ontario} \hfill London, ON \\
\noindent \textit{Bachelor of Science, Specialization in Computer Science} \hfill Expected July 2026 \\
\noindent \textit{Relevant Coursework: Operating Systems, Distributed Systems, Data Structures \& Algorithms, Database Systems}

\vspace{5pt}
\noindent{\large \textbf{Technical Skills}} \\
\vspace{-9pt}
\hrule
\vspace{4pt}
\noindent \textbf{Languages:} Python, Java, TypeScript, JavaScript, C++, SQL (PostgreSQL, MySql), HTML/CSS. \\
\noindent \textbf{Frameworks \& Libraries:} FastAPI, LangGraph, Spring Boot, Node.js, React, Next.js, REST APIs, TensorFlow. \\
\noindent \textbf{Testing \& Automation:} Pytest, Unittest, Robot Framework, Regression Testing, Test Automation, Integration Testing. \\
\noindent \textbf{Cloud \& DevOps:} Git, GitHub Actions, CI/CD Pipelines, Docker, Kubernetes, Jenkins, AWS (EC2, S3), Linux (CLI). \\
\noindent \textbf{Concepts:} OOP, Software Quality Assurance, Debugging, Test Driven Development (TDD), Agile/Scrum, IBM Z (Certified).

\vspace{5pt}
\noindent{\large \textbf{Experience}} \\
\vspace{-9pt}
\hrule
\vspace{4pt}
\noindent \textbf{Headstarter AI} \hfill Jul 2024 - Sep 2024 \\
\noindent \textbf{Software Engineering Fellow}
\begin{itemize}
    \item """ + exp_b[0] + r"""
    \item """ + exp_b[1] + r"""
    \item """ + exp_b[2] + r"""
    \item """ + exp_b[3] + r"""
\end{itemize}
\vspace{3pt}
\noindent \textbf{ZippiAI Inc.} \hfill Jun 2024 - Aug 2024 \\
\noindent \textbf{Data Engineer Intern}
\begin{itemize}
    \item """ + exp_b[4] + r"""
    \item """ + exp_b[5] + r"""
    \item """ + exp_b[6] + r"""
\end{itemize}

\vspace{5pt}
\noindent{\large \textbf{Projects}} \\
\vspace{-9pt}
\hrule
\vspace{4pt}
\noindent \textbf{AI Log Detective \& SRE Observability Platform (Sentinel)} \hfill \textit{Python, LangGraph, FastAPI, PostgreSQL}
\begin{itemize}
    \item """ + proj_b[0] + r"""
    \item """ + proj_b[1] + r"""
    \item """ + proj_b[2] + r"""
\end{itemize}
\vspace{4pt}
\noindent \textbf{Automated Test Framework \& Validation Utility} \hfill \textit{Python, Pytest, Git, Test Automation}
\begin{itemize}
    \item """ + proj_b[3] + r"""
    \item """ + proj_b[4] + r"""
    \item """ + proj_b[5] + r"""
\end{itemize}
\vspace{4pt}
\noindent \textbf{Real-Time ML Monitoring Engine (Aeon)} \hfill \textit{Python, Scikit-learn, TensorFlow, PostgreSQL}
\begin{itemize}
    \item """ + proj_b[6] + r"""
    \item """ + proj_b[7] + r"""
    \item """ + proj_b[8] + r"""
\end{itemize}

\end{document}
"""
    return template

def run_application_pipeline(portal_url: str, raw_jd_text: str, is_internship: bool = True):
    print("\n🚀 Initializing ApplyVault direct personal user token core...")
    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    creds = get_user_google_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    
    base_resume = load_base_resume(is_internship=is_internship)
    print("📡 Querying Claude Sonnet 4.6 Optimization Matrix...")
    optimized_data = generate_tailored_resume_content(anthropic_client, base_resume, raw_jd_text)
    
    company = optimized_data.get("company_name", "Target_Company")
    title = optimized_data.get("job_title", "Software_Engineer")
    score = optimized_data.get("ats_score", "72")
    
    print("✍️ Generating typesetting LaTeX file modules...")
    latex_code = build_latex_template(base_resume, optimized_data)
    
    clean_company = company.replace(" ", "_").replace("/", "_").replace("\\", "_")
    clean_title = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
    
    file_base = f"Krissh_Patel_{clean_title}_{clean_company}"
    tex_filename = f"{file_base}.tex"
    pdf_filename = f"{file_base}.pdf"
    
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)
        
    print("🛠️ Compiling LaTeX directly into recruiter-ready binary PDF format...")
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except Exception as err:
        print(f"❌ Compiler Warning: {err}")

    if not os.path.exists(pdf_filename):
        print("❌ Critical Compilation Breakout: Target PDF was not generated.")
        return

    print(f"☁️ Uploading {pdf_filename} securely using personal account storage...")
    file_metadata = {"name": pdf_filename, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(pdf_filename, mimetype="application/pdf", resumable=False)
    
    try:
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        file_id = uploaded_file.get("id")
    finally:
        if hasattr(media, '_fd') and media._fd:
            try: media._fd.close()
            except Exception: pass

    shareable_link = f"https://drive.google.com/file/d/{file_id}/view"
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    new_row_payload = [[current_date, company, title, portal_url, f"{score}%", shareable_link]]
    
    print("📊 Recording metrics row into Job Application Tracker Sheet...")
    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:F",
        valueInputOption="USER_ENTERED",
        body={"values": new_row_payload}
    ).execute()
    
    for ext in [".tex", ".pdf", ".aux", ".log", ".out"]:
        temp_file = f"{file_base}{ext}"
        if os.path.exists(temp_file):
            try: os.remove(temp_file)
            except Exception: pass
            
    print(f"🎉 Success! Beautiful 1-Page Resume logged for {company} in your Master Sheet.")

if __name__ == "__main__":
    print("\n=======================================================")
    print(" 🛠️  APPLYVAULT DYNAMIC APPLICATOR MATRIX INTERFACE  🛠️ ")
    print("=======================================================\n")
    portal_url = input("🔗 Paste Target Job Application URL: ").strip()
    if not portal_url:
        print("❌ Error: Application URL cannot be blank.")
        sys.exit(1)
        
    print("\n📝 Paste the Job Description text block below.")
    print("👉 (When finished pasting, press Enter, then Ctrl+Z on Windows on a blank line to run):")
    print("-------------------------------------------------------------------------------------------------------")
    raw_jd_lines = sys.stdin.read()
    raw_jd_text = raw_jd_lines.strip()
    
    if not raw_jd_text:
        print("❌ Error: Job Description text cannot be blank.")
        sys.exit(1)
        
    run_application_pipeline(portal_url, raw_jd_text, is_internship=True)