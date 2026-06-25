def load_base_resume(is_internship: bool = True) -> dict:
    """
    Returns the real-world structured components of Krissh Patel's resume.
    Conditional logic automatically handles Master's inclusion for internships.
    """
    profile = {
        "name": "Krissh Patel",
        "email": "krishpatel6524@gmail.com",
        "links": "linkedin.com/in/krissh-patel | github.com/imkrisshpatel",
        "skills": "Languages: Python, Java, TypeScript, JavaScript, C++, SQL (PostgreSQL, MySQL), HTML/CSS. Testing \\& Automation: Pytest, Unittest, Robot Framework, Regression Testing, Test Automation, Integration Testing. Frameworks \\& Libraries: FastAPI, LangGraph, Spring Boot, Node.js, React, Next.js, REST APIs, TensorFlow. Cloud \\& DevOps: Git, GitHub Actions, CI/CD Pipelines, Docker, Kubernetes, Jenkins, AWS (EC2, S3), Linux (CLI). Concepts: OOP, Software Quality Assurance, Debugging, Test Driven Development (TDD), Agile/Scrum, IBM Z (Certified).",
        "experience": [
            {
                "company": "Headstarter AI",
                "role": "Software Engineering Fellow",
                "timeline": "Jul 2024 -- Sep 2024",
                "bullets": [
                    "Developed Python-based test automation scripts to streamline regression testing, improving test cycle efficiency by 30%.",
                    "Reduced CI/CD deployment errors by 15% by refactoring automated testing scripts and CI/CD pipeline configurations alongside senior engineers from Amazon and Bloomberg.",
                    "Built and shipped 3+ full-stack AI applications serving 500+ users with React and Node.js, achieving 98% unit test coverage with Jest across all core service modules.",
                    "Authored internal API documentation and sprint artifacts, cutting engineer onboarding time by 20% and improving delivery velocity across a distributed cross-functional team."
                ]
            },
            {
                "company": "ZippiAI Inc.",
                "role": "Data Engineer Intern",
                "timeline": "Jun 2024 -- Aug 2024",
                "bullets": [
                    "Architected scalable Python-based automation ETL pipelines using SQL, increasing user engagement by 35% through data-driven feature prioritization.",
                    "Built Python automation scripts with integrated unit testing to streamline client onboarding and CRM synchronization, saving 10+ hours of manual work weekly while maintaining 100% data integrity.",
                    "Optimized PostgreSQL schema designs and complex SQL queries for a 3,000+ client database, reducing API response latency by 15% through indexing and OOP-based query abstraction."
                ]
            }
        ],
        "projects": [
            {
                "title": "AI Log Detective \\& SRE Observability Platform (Sentinel)",
                "tech": "Python, LangGraph, FastAPI, PostgreSQL",
                "bullets": [
                    "Engineered a multi-agent SRE observability platform with stateful LangGraph workflows to automate root cause analysis, reducing system downtime by 40%.",
                    "Built a high-concurrency ingestion engine using Python Asyncio to process 100+ simultaneous telemetry feeds and generate RCA reports in under 5 seconds end-to-end.",
                    "Integrated LLM agents via MCP SDK to map anomalous log patterns to source code locations, automating patch generation and cutting manual debugging time by 30%."
                ]
            },
            {
                "title": "Automated Test Framework \\& Validation Utility",
                "tech": "Python, Pytest, Git, Test Automation",
                "bullets": [
                    "Designed and built an open-source test automation framework in Python utilizing structural object-oriented principles to execute end-to-end testing scripts.",
                    "Implemented automated log parsing, data sanitization scripts, and edge-case verification modules to intercept software execution anomalies with 100% precision.",
                    "Configured a localized version version control pipeline using Git to log test iteration results, run programmatic debugging steps, and generate automated test execution reports."
                ]
            },
            {
                "title": "Real-Time ML Monitoring Engine (Aeon)",
                "tech": "Python, Scikit-learn, TensorFlow, PostgreSQL",
                "bullets": [
                    "Built a supervised ML pipeline to detect equipment corrosion from sensor telemetry using data structures \\& algorithms principles, improving predictive accuracy by 20% over baseline.",
                    "Processed 1TB+ of structured sensor data with optimized SQL schemas and indexed queries, reducing training data retrieval time by 60% and enabling real-time inference at scale.",
                    "Implemented model drift detection scripts triggering automated retraining via cron orchestration, sustaining a 15% improvement in equipment reliability over a 6-month production window."
                ]
            }
        ]
    }

    # Handle structural education parameters
    education = [
        "{\\bf University of Western Ontario} \\hfill London, ON \\\\ Bachelor of Science, Specialization in Computer Science \\hfill Expected July 2026 \\\\ \\it{Achievements: Western Scholarship of Distinction} \\\\ \\it{Relevant Coursework: Operating Systems, Distributed Systems, Data Structures \\& Algorithms, Database Systems}"
    ]
    if is_internship:
        education.insert(0, "{\\bf Toronto Metropolitan University} \\hfill Toronto, ON \\\\ Master of Engineering (M.Eng.), Electrical and Computer Engineering \\hfill Sep 2026 -- Present \\\\ \\it{Concentration: Artificial Intelligence}")
        
    profile["education_latex"] = " \\\\ \\vspace{4pt} \n".join(education)
    return profile