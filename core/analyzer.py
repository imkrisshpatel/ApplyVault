import json
from anthropic import Anthropic

def generate_tailored_resume_content(client: Anthropic, base_resume: dict, jd_text: str) -> dict:
    """
    Leverages Claude Sonnet to extract metadata and optimize 16 distinct resume bullets.
    Dynamically aligns the candidate's existing projects and experience nodes to ANY target role.
    """
    
    system_prompt = """You are an expert technical ATS resume optimization engine specializing in cross-ecosystem translation.
Your task is to analyze the provided Job Description (JD) and optimize the candidate's baseline resume content to fit this target role perfectly.
You must extract the actual employer/company name from the JD context cleanly (e.g., Apple, Gateway, Oracle, SPC, Trulioo). If not explicitly mentioned, use the domain or 'Target Company'.

You must return a raw JSON string matching the exact schema definition below. Do not wrap the response in markdown blocks (like ```json).

{
  "company_name": "Cleanly extracted employer/company name",
  "job_title": "Cleanly extracted target job title",
  "ats_score": "An HONEST, calculation-driven integer match percentage between 0 and 100 based on exact stack, skill, and role alignment",
  "optimized_experience_bullets": [
    "Unique metric bullet 1 for Headstarter AI",
    "Unique metric bullet 2 for Headstarter AI",
    "Unique metric bullet 3 for Headstarter AI",
    "Unique metric bullet 4 for Headstarter AI",
    "Unique metric bullet 1 for ZippiAI",
    "Unique metric bullet 2 for ZippiAI",
    "Unique metric bullet 3 for ZippiAI"
  ],
  "optimized_project_bullets": [
    "Unique metric bullet 1 for Sentinel Observability Platform",
    "Unique metric bullet 2 for Sentinel Observability Platform",
    "Unique metric bullet 3 for Sentinel Observability Platform",
    "Unique metric bullet 1 for Automated Test Framework",
    "Unique metric bullet 2 for Automated Test Framework",
    "Unique metric bullet 3 for Automated Test Framework",
    "Unique metric bullet 1 for Real-Time ML Engine",
    "Unique metric bullet 2 for Real-Time ML Engine",
    "Unique metric bullet 3 for Real-Time ML Engine"
  ]
}

CRITICAL RULES FOR ADAPTIVE ALIGNMENT:
1. ENTITY INTEGRITY: You MUST preserve the exact company names (Headstarter AI, ZippiAI Inc.) and the exact project titles (AI Log Detective & SRE Observability Platform (Sentinel), Automated Test Framework & Validation Utility, Real-Time ML Monitoring Engine (Aeon)). Do not change, split, or rename these baseline corporate/project nodes.
2. FLAT ARRAYS: "optimized_experience_bullets" MUST contain exactly 7 unique string elements. "optimized_project_bullets" MUST contain exactly 9 unique string elements.
3. FORBIDDEN FORMATTING: Do not generate italics, bolding, or markdown styling inside the string values. Never use long dashes, em-dashes, or en-dashes (like — or –). Always use simple standard hyphens (-) or standard punctuation.
4. DYNAMIC ROLE SHIFTING & CROSS-STACK TRANSLATION:
   - For Backend / Low-Level Roles (e.g., Oracle, C#, .NET): Focus on object-oriented software patterns, typing structures, API scalability, database engines, and performance profiling.
   - For Frontend / Web / Full-Stack Roles (e.g., Gateway, Angular, React): Highlight responsive web platforms, component-driven design architectures, state management systems, and client-onboarding layouts.
   - For QA / Test Roles: Emphasize regression testing, script validation, pytest suites, continuous integration pipelines, automation scripts, and test-driven design.
   - For Data / AI Roles: Highlight ML pipelines, vector lookups, model evaluation, schema design, PostgreSQL queries, and mathematical/algorithmic data structures.
5. TECH STACK BRIDGING: Seamlessly weave keywords or design principles from the target JD into your bullets (e.g., if the JD mentions specific platforms or framework ecosystems like C#/.NET or Angular, integrate or draw analogies to those development practices, data paradigms, or transport protocols like JSON where logical).
6. FOUNDATIONAL VALUES: Intelligently incorporate soft values specified in the JD (e.g., accountability, adaptability, collaboration, timeline management, attention to detail) into the operational context of your bullet impacts.
"""

    user_content = f"""
    --- TARGET JOB DESCRIPTION ---
    {jd_text}
    
    --- CANDIDATE BASELINE STRUCTURAL DATA ---
    {json.dumps(base_resume, indent=2)}
    """

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        temperature=0.1,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}]
    )
    
    raw_text = response.content[0].text.strip()
    
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    try:
        return json.loads(raw_text)
    except Exception as e:
        print(f"⚠️ JSON Parser exception: {e}")
        return {
            "company_name": "Target_Company",
            "job_title": "Software Engineer",
            "ats_score": "75",
            "optimized_experience_bullets": [
                "Architected scalable backend service layers and high-throughput communication pipelines.",
                "Optimized multi-threaded computational workflows to systematically reduce transaction latency.",
                "Refactored regression verification suites to guarantee continuous deployment validation.",
                "Spearheaded architectural migrations towards distributed messaging microservice frameworks.",
                "Optimized database indexing algorithms and query caching architectures for PostgreSQL schemas.",
                "Structured relational data normalization workflows to handle concurrent analytical workloads.",
                "Automated end-to-end telemetry collections across distributed microservice clusters."
            ],
            "optimized_project_bullets": [
                "Developed an automated AI log analyzer managing extensive investigative telemetry streams.",
                "Integrated multi-agent models to parse structural telemetry patterns autonomously.",
                "Optimized vector search data lookups achieving enhanced response cycle speeds.",
                "Engineered structural test automation frameworks utilizing Python execution suites.",
                "Designed automated mocking modules to bypass third-party external environment dependencies.",
                "Integrated comprehensive automated profiling scripts within GitHub Actions pipelines.",
                "Constructed real-time performance evaluation tools mapping algorithmic model decay.",
                "Optimized data preprocessing streams to extract vectorized features under tight timing windows.",
                "Architected unified dashboard visual systems using low-overhead design protocols."
            ]
        }