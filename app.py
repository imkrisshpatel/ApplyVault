"""
app.py — ApplyVault Pipeline Orchestrator
Coordinates: analysis → generation → LaTeX build → PDF → Google Drive → Sheets log
"""

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

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ---------------------------------------------------------------------------
# GOOGLE AUTH
# ---------------------------------------------------------------------------

def get_user_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = UserCredentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Missing 'credentials.json' in root directory.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


# ---------------------------------------------------------------------------
# LATEX BUILDER
# ---------------------------------------------------------------------------

def sanitize_latex(text: str) -> str:
    """Escapes LaTeX special characters in generated bullet strings."""
    text = text.replace("\\&", "__AMP__").replace("&", "\\&").replace("__AMP__", "\\&")
    text = text.replace("\\%", "__PCT__").replace("%", "\\%").replace("__PCT__", "\\%")
    text = text.replace("\\_", "__UND__").replace("_", "\\_").replace("__UND__", "\\_")
    text = text.replace("#", "\\#")
    text = text.replace("$", "\\$")
    text = text.replace("^", "\\^{}")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("—", "-").replace("–", "-")
    return text


def build_skills_block(matched_skills: dict, optimized_order: list) -> str:
    """Renders only the JD-matched skills in relevance order."""
    default_order = list(matched_skills.keys())
    order = optimized_order if optimized_order else default_order
    all_categories = order + [c for c in default_order if c not in order]

    lines = []
    for category in all_categories:
        if category in matched_skills and matched_skills[category]:
            value = matched_skills[category]
            skills_str = ", ".join(value) if isinstance(value, list) else value
            safe_category = category.replace("&", "\\&")
            lines.append(f"\\noindent \\textbf{{{safe_category}:}} {skills_str}. \\\\")
    return "\n".join(lines)


def build_education_block(education: list) -> str:
    """Renders education entries from structured list."""
    blocks = []
    for edu in education:
        block = (
            f"\\noindent \\textbf{{{edu['institution']}}} \\hfill {edu['location']} \\\\\n"
            f"\\noindent \\textit{{{edu['degree']}}} \\hfill {edu['timeline']} \\\\\n"
            f"\\noindent \\textit{{{edu['details']}}}"
        )
        blocks.append(block)
    return "\n\n\\vspace{4pt}\n".join(blocks)


def build_latex_template(base: dict, ai_data: dict) -> str:
    """
    Assembles the full LaTeX resume.
    Projects appear in JD-relevance order from Pass 1 selection.
    Skills appear in JD-relevance order from Pass 2 output.
    """

    # --- Experience bullets ---
    exp_bullets_raw = ai_data.get("optimized_experience_bullets", [])
    exp_bullets = [sanitize_latex(str(b)) for b in exp_bullets_raw]
    while len(exp_bullets) < 7:
        exp_bullets.append("Delivered software components aligned with engineering team objectives.")

    # --- Project bullets (keyed by project id) ---
    proj_bullets_map = ai_data.get("optimized_project_bullets", {})

    # --- Selected projects in relevance order ---
    selected_ids = ai_data.get("selected_project_ids", [])
    all_projects = {p["id"]: p for p in base.get("projects", [])}
    selected_projects = [all_projects[pid] for pid in selected_ids if pid in all_projects]

    # --- Skills block: full inventory always shown + any JD-specific additions merged in ---
    full_skills = {k: list(v) for k, v in base.get("skills_inventory", {}).items()}
    for category, extras in ai_data.get("additional_skills", {}).items():
        if category in full_skills:
            for item in extras:
                if item not in full_skills[category]:
                    full_skills[category].append(item)
        elif extras:
            full_skills[category] = list(extras)
    skills_order = ai_data.get("skills_category_order", [])
    skills_block = build_skills_block(full_skills, skills_order)

    # --- Education block ---
    education_block = build_education_block(base.get("education", []))

    # --- Build project LaTeX blocks ---
    project_latex_blocks = []
    for proj in selected_projects:
        pid = proj["id"]
        bullets_raw = proj_bullets_map.get(pid, proj.get("bullets", []))
        bullets = [sanitize_latex(str(b)) for b in bullets_raw]
        while len(bullets) < 3:
            bullets.append("Delivered core system features with measurable production impact.")

        title_escaped = proj["title"]
        tech = proj.get("tech", "")

        block = (
            f"\\noindent \\textbf{{{title_escaped}}} \\hfill \\textit{{{tech}}}\n"
            f"\\begin{{itemize}}\n"
            + "".join(f"    \\item {b}\n" for b in bullets[:3])
            + "\\end{itemize}\n\\vspace{2pt}"
        )
        project_latex_blocks.append(block)

    projects_latex = "\n".join(project_latex_blocks)

    # --- Assemble full document ---
    template = (
        r"""\documentclass[letterpaper,10pt]{article}
\usepackage{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{marvosym}
\usepackage{fontawesome5}

% Strict single-page margin configuration
\geometry{letterpaper, margin=0.35in, top=0.35in, bottom=0.35in}
\pagestyle{empty}

\setlength{\emergencystretch}{3em}
\hyphenpenalty=5000
\exhyphenpenalty=5000
\setlist[itemize]{leftmargin=*, noitemsep, topsep=0pt, parsep=0pt, partopsep=0pt}

\begin{document}

% ---- HEADER ----
\begin{center}
    {\Huge \textbf{Krissh Patel}} \\ \vspace{2pt}
    \small
    \href{mailto:krisshpatel37@gmail.com}{\raisebox{-0.1ex}{\Letter}\ krisshpatel37@gmail.com} \ | \
    \href{https://linkedin.com/in/krissh-patel}{\raisebox{-0.1ex}{\faLinkedin}\ linkedin.com/in/krissh-patel} \ | \
    \href{https://github.com/imkrisshpatel}{\raisebox{-0.1ex}{\faGithub}\ github.com/imkrisshpatel}
\end{center}

% ---- EDUCATION ----
\vspace{-6pt}
\noindent{\large \textbf{Education}} \\
\vspace{-9pt}
\hrule
\vspace{3pt}
"""
        + education_block
        + r"""

% ---- TECHNICAL SKILLS ----
\vspace{4pt}
\noindent{\large \textbf{Technical Skills}} \\
\vspace{-9pt}
\hrule
\vspace{3pt}
"""
        + skills_block
        + r"""

% ---- EXPERIENCE ----
\vspace{4pt}
\noindent{\large \textbf{Experience}} \\
\vspace{-9pt}
\hrule
\vspace{3pt}
\noindent \textbf{Headstarter AI} \hfill Jul 2024 - Sep 2024 \\
\noindent \textbf{Software Engineering Fellow}
\begin{itemize}
    \item """
        + exp_bullets[0] + r"""
    \item """ + exp_bullets[1] + r"""
    \item """ + exp_bullets[2] + r"""
    \item """ + exp_bullets[3] + r"""
\end{itemize}
\vspace{2pt}
\noindent \textbf{ZippiAI Inc.} \hfill Jun 2024 - Aug 2024 \\
\noindent \textbf{Data Engineer Intern}
\begin{itemize}
    \item """ + exp_bullets[4] + r"""
    \item """ + exp_bullets[5] + r"""
    \item """ + exp_bullets[6] + r"""
\end{itemize}

% ---- PROJECTS ----
\vspace{4pt}
\noindent{\large \textbf{Projects}} \\
\vspace{-9pt}
\hrule
\vspace{3pt}
"""
        + projects_latex
        + r"""

\end{document}
"""
    )

    return template


# ---------------------------------------------------------------------------
# FIND NEXT EMPTY ROW — ignores Status column G entirely
# ---------------------------------------------------------------------------

def get_next_empty_row(sheets_service) -> int:
    """
    Reads only columns A:F to find the next empty row.
    Ignores column G (Status) entirely so dropdown formatting
    never pushes the append position down.
    """
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:F"
        ).execute()
        values = result.get("values", [])
        # Next empty row is one after the last row with data
        return len(values) + 1
    except Exception:
        # Safe fallback — start after headers if read fails
        return 2


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def run_application_pipeline(portal_url: str, raw_jd_text: str, is_internship: bool = True):
    print("\n🚀 Initializing ApplyVault pipeline...")

    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    creds = get_user_google_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Load base resume data
    base_resume = load_base_resume(is_internship=is_internship)

    # Run two-pass AI pipeline
    optimized_data = generate_tailored_resume_content(anthropic_client, base_resume, raw_jd_text)

    if not optimized_data:
        print("❌ Pipeline aborted — no optimization data returned.")
        return

    company  = optimized_data.get("company_name", "Target_Company")
    title    = optimized_data.get("job_title", "Software_Engineer")
    score    = optimized_data.get("ats_score", "??")
    domain   = optimized_data.get("domain_archetype", "UNKNOWN")
    keywords = optimized_data.get("ats_keywords_injected", [])

    print(f"\n✅ Analysis complete:")
    print(f"   Company     : {company}")
    print(f"   Role        : {title}")
    print(f"   Domain      : {domain}")
    print(f"   ATS Score   : {score}/100")
    print(f"   Keywords in : {', '.join(keywords)}")

    # Build LaTeX
    print("\n✍️  Building LaTeX resume...")
    latex_code = build_latex_template(base_resume, optimized_data)

    clean_company = company.replace(" ", "_").replace("/", "_").replace("\\", "_")
    clean_title   = title.replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_base     = f"Krissh_Patel_{clean_title}_{clean_company}"
    tex_filename  = f"{file_base}.tex"
    pdf_filename  = f"{file_base}.pdf"

    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_code)

    # Compile PDF
    print("🛠️  Compiling PDF via pdflatex...")
    compile_success = False
    try:
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        compile_success = True
        print("✅ PDF compiled successfully.")
    except subprocess.CalledProcessError:
        if os.path.exists(pdf_filename):
            compile_success = True
            print("✅ PDF compiled successfully (MiKTeX update reminder — not a real error).")
            print("   Tip: Open MiKTeX Console and install updates to suppress this warning.")
        else:
            print("❌ PDF was not generated. Real LaTeX error — check your .tex file.")
    except FileNotFoundError:
        print("❌ pdflatex not found. Is MiKTeX or TeX Live installed and on your PATH?")

    if not compile_success or not os.path.exists(pdf_filename):
        if os.path.exists(tex_filename):
            os.remove(tex_filename)
        return

    # Upload to Google Drive
    print(f"\n☁️  Uploading {pdf_filename} to Google Drive...")
    file_metadata = {"name": pdf_filename, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(pdf_filename, mimetype="application/pdf", resumable=False)

    file_id = None
    try:
        uploaded = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        file_id = uploaded.get("id")
        print("✅ Uploaded successfully.")
    except Exception as e:
        print(f"❌ Google Drive upload failed: {e}")
    finally:
        if hasattr(media, "_fd") and media._fd:
            try:
                media._fd.close()
            except Exception:
                pass

    if not file_id:
        print("❌ Upload failed — skipping Sheets log.")
        return

    shareable_link = f"https://drive.google.com/file/d/{file_id}/view"

    # Find next empty row based on A:F only — ignores Status column G dropdown
    next_row = get_next_empty_row(sheets_service)
    write_range = f"Sheet1!A{next_row}:F{next_row}"
    print(f"📊 Logging to Google Sheets row {next_row}...")

    # --- ADD THIS LINE TO DEFINE THE MISSING VARIABLE ---
    current_date = datetime.date.today().strftime("%Y-%m-%d")

    # Only write A:F — Status column G is handled manually
    row = [[
        current_date,       # A: Date Applied
        company,            # B: Company Name
        title,              # C: Job Title
        portal_url,         # D: Portal Link
        f"{score}%",        # E: ATS Score
        shareable_link,     # F: Tailored Resume Link
    ]]

    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=write_range,
            valueInputOption="USER_ENTERED",
            body={"values": row}
        ).execute()
        print(f"✅ Logged to Sheets row {next_row} successfully.")
    except Exception as e:
        print(f"❌ Google Sheets log failed: {e}")
        print(f"   Drive link (save this manually): {shareable_link}")

    # Cleanup temp files
    for ext in [".tex", ".aux", ".log", ".out", ".pdf"]:
        temp = f"{file_base}{ext}"
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except Exception:
                pass

    print(f"\n🎉 Done! Resume for {company} ({title}) logged to your tracker.")
    print(f"   Sheets row : {next_row}")
    print(f"   Drive link : {shareable_link}")
    print(f"   Domain     : {domain}")
    print(f"   Keywords   : {', '.join(keywords)}")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n=======================================================")
    print("  🛠️   APPLYVAULT  —  RESUME AUTOMATION PIPELINE  🛠️  ")
    print("=======================================================\n")

    portal_url = input("🔗 Paste the job application URL: ").strip()
    if not portal_url:
        print("❌ URL cannot be blank.")
        sys.exit(1)

    print("\n📝 Paste the Job Description below.")
    print("   When done: press Enter, then Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) on a blank line.\n")
    print("-" * 70)

    raw_jd_text = sys.stdin.read().strip()

    if not raw_jd_text:
        print("❌ Job description cannot be blank.")
        sys.exit(1)

    run_application_pipeline(portal_url, raw_jd_text, is_internship=True)