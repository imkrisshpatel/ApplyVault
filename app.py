import os
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
    """Authenticates the user directly to utilize their personal account storage quota."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = UserCredentials.from_authorized_user_file(TOKEN_FILE, google_scopes)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Missing 'credentials.json' configuration file in root directory.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", google_scopes)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def build_latex_template(base: dict, ai_data: dict) -> str:
    """Helper method to construct recruiter-grade typographic LaTeX code blocks safely."""
    exp_b = ai_data.get("optimized_experience_bullets", [])
    proj_b = ai_data.get("optimized_project_bullets", [])

    # Flatten out lists safely
    cleaned_exp = [str(item) for item in exp_b]
    cleaned_proj = [str(item) for item in proj_b]

    while len(cleaned_exp) < 7: cleaned_exp.append("Optimized system components using standard engineering methodologies.")
    while len(cleaned_proj) < 9: cleaned_proj.append("Engineered core features and structured test automation architectures.")

    def sanitize_for_latex(text: str) -> str:
        text = text.replace("\\&", "__AMP__").replace("&", "\\&").replace("__AMP__", "\\&")
        text = text.replace("\\%", "__PCT__").replace("%", "\\%").replace("__PCT__", "\\%")
        text = text.replace("\\_", "__UND__").replace("_", "\\_").replace("__UND__", "\\_")
        return text

    exp_b = [sanitize_for_latex(b) for b in cleaned_exp]
    proj_b = [sanitize_for_latex(b) for b in cleaned_proj]
    base_skills = sanitize_for_latex(base["skills"])
    base_education = sanitize_for_latex(base["education_latex"])

    template = r"""\documentclass[letterpaper,10pt]{article}
\usepackage{geometry}
\usepackage[hidelinks]{hyperref}

\geometry{letterpaper, margin=0.5in}
\pagestyle{empty}

\begin{document}
\begin{center}
    {\Huge \textbf{""" + base["name"] + r"""}} \\ \vspace{3pt}
    \small """ + base["email"] + r""" | """ + base["links"] + r"""
\end{center}

\vspace{5pt}
\noindent{\large \textbf{\textsc{Education}}} \\
\vspace{-8pt}
\hrule
\vspace{4pt}
""" + base_education + r"""

\vspace{8pt}
\noindent{\large \textbf{\textsc{Technical Skills}}} \\
\vspace{-8pt}
\hrule
\vspace{4pt}
\small{""" + base_skills + r"""}

\vspace{8pt}
\noindent{\large \textbf{\textsc{Experience}}} \\
\vspace{-8pt}
\hrule
\vspace{4pt}
\noindent \textbf{""" + base["experience"][0]["company"] + r"""} \hfill """ + base["experience"][0]["timeline"] + r""" \\
\noindent \textit{""" + base["experience"][0]["role"] + r"""}
\begin{itemize}
    \setlength{\itemsep}{1pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
    \item """ + exp_b[0] + r"""
    \item """ + exp_b[1] + r"""
    \item """ + exp_b[2] + r"""
    \item """ + exp_b[3] + r"""
\end{itemize}
\vspace{4pt}
\noindent \textbf{""" + base["experience"][1]["company"] + r"""} \hfill """ + base["experience"][1]["timeline"] + r""" \\
\noindent \textit{""" + base["experience"][1]["role"] + r"""}
\begin{itemize}
    \setlength{\itemsep}{1pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
    \item """ + exp_b[4] + r"""
    \item """ + exp_b[5] + r"""
    \item """ + exp_b[6] + r"""
\end{itemize}

\vspace{8pt}
\noindent{\large \textbf{\textsc{Projects}}} \\
\vspace{-8pt}
\hrule
\vspace{4pt}
\noindent \textbf{""" + base["projects"][0]["title"] + r"""} \hfill \textit{""" + base["projects"][0]["tech"] + r"""}
\begin{itemize}
    \setlength{\itemsep}{1pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
    \item """ + proj_b[0] + r"""
    \item """ + proj_b[1] + r"""
    \item """ + proj_b[2] + r"""
\end{itemize}
\vspace{4pt}
\noindent \textbf{""" + base["projects"][1]["title"] + r"""} \hfill \textit{""" + base["projects"][1]["tech"] + r"""}
\begin{itemize}
    \setlength{\itemsep}{1pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
    \item """ + proj_b[3] + r"""
    \item """ + proj_b[4] + r"""
    \item """ + proj_b[5] + r"""
\end{itemize}
\vspace{4pt}
\noindent \textbf{""" + base["projects"][2]["title"] + r"""} \hfill \textit{""" + base["projects"][2]["tech"] + r"""}
\begin{itemize}
    \setlength{\itemsep}{1pt}
    \setlength{\parskip}{0pt}
    \setlength{\parsep}{0pt}
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
    
    company = optimized_data.get("company_name", "Unknown_Company")
    title = optimized_data.get("job_title", "Software Engineer")
    score = optimized_data.get("ats_score", "85")
    
    print("✍️ Generating typesetting LaTeX file modules...")
    latex_code = build_latex_template(base_resume, optimized_data)
    
    clean_company_name = company.replace(" ", "_").replace("/", "_").replace("\\", "_")
    tex_filename = f"Resume_{clean_company_name}.tex"
    pdf_filename = f"Resume_{clean_company_name}.pdf"
    
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
        # HARD FIX: Explicitly close the internal Windows file pointer stream immediately
        if hasattr(media, '_fd') and media._fd:
            try:
                media._fd.close()
            except Exception:
                pass

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
    
    # Clean up local run artifacts since file handles are officially released
    for ext in [".tex", ".pdf", ".aux", ".log", ".out"]:
        temp_file = f"Resume_{clean_company_name}{ext}"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"⚠️ Cleanup warning for item {temp_file}: {e}")
            
    print(f"🎉 Success! Beautiful LaTeX PDF resume logged for {company} in your Master Sheet.")

if __name__ == "__main__":
    sample_url = "https://careers.amd.com/jobs/junior-engineer"
    sample_jd = "Looking for a Junior Software Engineer with deep knowledge of Python, PostgreSQL schema optimizations, and automated script testing patterns."
    
    run_application_pipeline(sample_url, sample_jd, is_internship=True)