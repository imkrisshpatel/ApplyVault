"""
parser.py — ApplyVault Candidate Data Layer
Stores Krissh's full base resume as structured data.
As projects/experience grow, add them here and the 
selection logic in analyzer.py will pick the best subset.
"""


def load_base_resume(is_internship: bool = True) -> dict:
    """
    Returns the structured baseline resume for Krissh Patel.
    All projects live here — analyzer.py selects the best 3 per JD.
    Add new experiences and projects to this file over time.
    """

    profile = {
        "name": "Krissh Patel",
        "email": "krisshpatel37@gmail.com",
        "links": "linkedin.com/in/krissh-patel | github.com/imkrisshpatel",

        # Master skills inventory — Pass 1 selects only what matches each JD
        "skills_inventory": {
            "Languages": ["Python", "Java", "TypeScript", "JavaScript", "C++", "SQL", "HTML/CSS"],
            "Frameworks & Libraries": ["FastAPI", "LangGraph", "Spring Boot", "Node.js", "React", "Next.js", "REST APIs", "TensorFlow", "PyTorch", "Scikit-learn"],
            "Testing & Automation": ["Pytest", "Unittest", "Robot Framework", "Regression Testing", "Test Automation", "Integration Testing", "TDD"],
            "Cloud & DevOps": ["Git", "GitHub Actions", "CI/CD Pipelines", "Docker", "Kubernetes", "Jenkins", "AWS (EC2, S3)", "Linux (CLI)"],
            "Concepts": ["OOP", "Software Quality Assurance", "Debugging", "Agile/Scrum", "IBM Z (Certified)", "Machine Learning", "NLP"]
        },

        "experience": [
            {
                "company": "Headstarter AI",
                "role": "Software Engineering Fellow",
                "timeline": "Jul 2024 -- Sep 2024",
                "bullets": [
                    "Developed Python-based test automation scripts to streamline regression testing, improving test cycle efficiency by 30%.",
                    "Reduced CI/CD deployment errors by 15% by refactoring automated testing scripts and pipeline configurations alongside senior engineers from Amazon and Bloomberg.",
                    "Built and shipped 3+ full-stack AI applications serving 500+ users with React and Node.js, achieving 98% unit test coverage with Jest across all core service modules.",
                    "Authored internal API documentation and sprint artifacts, cutting engineer onboarding time by 20% and improving delivery velocity across a distributed cross-functional team."
                ]
            },
            {
                "company": "ZippiAI Inc.",
                "role": "Data Engineer Intern",
                "timeline": "Jun 2024 -- Aug 2024",
                "bullets": [
                    "Architected scalable Python-based ETL automation pipelines using SQL, increasing user engagement by 35% through data-driven feature prioritization.",
                    "Built Python automation scripts with integrated unit testing to streamline client onboarding and CRM synchronization, saving 10+ hours of manual work weekly while maintaining 100% data integrity.",
                    "Optimized PostgreSQL schema designs and complex SQL queries for a 3,000+ client database, reducing API response latency by 15% through indexing and OOP-based query abstraction."
                ]
            }
        ],

        # All projects live here. Analyzer picks best 3 per JD.
        # Add new projects below as you build them — never remove old ones.
        "projects": [
            {
                "id": "sentinel",
                "title": "AI Log Detective \\& SRE Observability Platform (Sentinel)",
                "tech": "Python, LangGraph, FastAPI, PostgreSQL",
                "domain_tags": ["BACKEND_SYSTEMS", "CLOUD_DEVOPS", "DATA_ML"],
                "bullets": [
                    "Engineered a multi-agent SRE observability platform with stateful LangGraph workflows to automate root cause analysis, reducing system downtime by 40%.",
                    "Built a high-concurrency ingestion engine using Python Asyncio to process 100+ simultaneous telemetry feeds and generate RCA reports in under 5 seconds end-to-end.",
                    "Integrated LLM agents via MCP SDK to map anomalous log patterns to source code locations, automating patch generation and cutting manual debugging time by 30%."
                ]
            },
            {
                "id": "test_framework",
                "title": "Automated Test Framework \\& Validation Utility",
                "tech": "Python, Pytest, Git, Test Automation",
                "domain_tags": ["QA_AUTOMATION", "BACKEND_SYSTEMS"],
                "bullets": [
                    "Designed and built an open-source test automation framework in Python utilizing object-oriented principles to execute end-to-end testing scripts across multiple software modules.",
                    "Implemented automated log parsing, data sanitization scripts, and edge-case verification modules to intercept software execution anomalies with 100% precision.",
                    "Configured a version-controlled test pipeline using Git to log test iteration results, run programmatic debugging steps, and generate automated test execution reports."
                ]
            },
            {
                "id": "aeon",
                "title": "Real-Time ML Monitoring Engine (Aeon)",
                "tech": "Python, Scikit-learn, TensorFlow, PostgreSQL",
                "domain_tags": ["DATA_ML", "BACKEND_SYSTEMS"],
                "bullets": [
                    "Built a supervised ML pipeline to detect equipment corrosion from sensor telemetry using Scikit-learn and TensorFlow, improving predictive accuracy by 20% over baseline.",
                    "Processed 1TB+ of structured sensor data with optimized PostgreSQL schemas and indexed SQL queries, reducing training data retrieval time by 60% and enabling real-time inference at scale.",
                    "Implemented model drift detection scripts triggering automated retraining via cron orchestration, sustaining a 15% improvement in equipment reliability over a 6-month production window."
                ]
            }

            # -------------------------------------------------------
            # ADD NEW PROJECTS BELOW AS YOU BUILD THEM
            # Copy the block structure above. Add relevant domain_tags
            # from: QA_AUTOMATION, BACKEND_SYSTEMS, FULL_STACK_WEB,
            #        DATA_ML, CLOUD_DEVOPS, FRONTEND_UI
            # -------------------------------------------------------
        ]
    }

    # Education block — MEng included only for internship applications
    education = []
    if is_internship:
        education.append({
            "institution": "Toronto Metropolitan University",
            "location": "Toronto, ON",
            "degree": "Master of Engineering (M.Eng.), Electrical and Computer Engineering",
            "timeline": "Sep 2026 -- Present",
            "details": "Concentration: Artificial Intelligence"
        })

    education.append({
        "institution": "University of Western Ontario",
        "location": "London, ON",
        "degree": "Bachelor of Science, Specialization in Computer Science",
        "timeline": "Expected July 2026",
        "details": "Relevant Coursework: Operating Systems, Distributed Systems, Data Structures \\& Algorithms, Database Systems"
    })

    profile["education"] = education
    return profile