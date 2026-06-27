"""
analyzer.py — ApplyVault AI Core Engine
Two-pass generation architecture:
  Pass 1: JD analysis — domain lock, keyword extraction, project selection
  Pass 2: Bullet generation — VOC rewrite, stack bridging, soft skill injection
"""

import json
import hashlib
import os
from anthropic import Anthropic


# ---------------------------------------------------------------------------
# JD CACHE — avoids duplicate API calls for the same job description
# Saved as flat .json files under cache/ directory
# ---------------------------------------------------------------------------

CACHE_DIR = "cache"

def _get_cache_key(jd_text: str) -> str:
    return hashlib.md5(jd_text.encode("utf-8")).hexdigest()

def _load_from_cache(jd_text: str):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{_get_cache_key(jd_text)}.json")
    if os.path.exists(cache_path):
        print("💾 Cache hit — loading saved analysis. Skipping API call.")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def _save_to_cache(jd_text: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{_get_cache_key(jd_text)}.json")
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# PASS 1 — JD ANALYSIS
# Classifies domain, extracts keywords, selects best projects, maps stack bridges
# ---------------------------------------------------------------------------

PASS1_SYSTEM = """You are an elite technical recruiting analyst and ATS systems expert.
Your task is to deeply analyze a Job Description and a candidate's project pool, 
then output a structured JSON analysis object.

Return ONLY raw JSON — no markdown, no backticks, no preamble.

OUTPUT SCHEMA:
{
  "company_name": "Clean employer name extracted from JD",
  "job_title": "Clean target job title from JD",
  "viable": true or false,
  "estimated_ceiling_score": integer 0-100,
  "rejection_reason": "If viable=false, explain the hard blocker. Otherwise empty string.",
  "domain_archetype": "One of: QA_AUTOMATION | BACKEND_SYSTEMS | FULL_STACK_WEB | DATA_ML | CLOUD_DEVOPS | FRONTEND_UI",
  "top_jd_verbs": ["5 exact architectural action verbs from the JD"],
  "ats_keywords": ["Top 8 exact-match keywords/tools/frameworks from JD — strings that must appear verbatim in the resume"],
  "soft_skills": ["3 soft skills named or implied by the JD"],
  "stack_bridges": {
    "jd_tech": "paradigm phrase to use in bullets when candidate lacks this exact tech"
  },
  "additional_skills": {
    "Frameworks & Libraries": ["JD-required tools/frameworks NOT already in the inventory that the candidate genuinely has exposure to"],
    "Concepts": ["JD-required concepts NOT in the inventory that the candidate can honestly claim"]
  },
  "selected_project_ids": ["3 project ids from the candidate pool ranked by JD relevance, most relevant first"],
  "project_relevance_scores": {
    "project_id": integer score 0-100
  },
  "skills_category_order": ["Ordered list of skills category names, most JD-relevant first — include ALL categories"]
}

ADDITIONAL SKILLS RULES:
- The candidate's full inventory is ALWAYS shown. Do NOT filter it down.
- Only add skills that appear in the JD AND are NOT already covered by any existing inventory item.
- Only add specific tool/technology names (e.g., "Kafka", "Temporal", "RLHF") — never abstract concept phrases (e.g., "Agile Delivery", "Event Streaming", "Workflow Orchestration").
- Do not add anything that is already implied by an existing item (e.g., do NOT add "Agile" if "Agile/Scrum" already exists).
- Only add skills the candidate genuinely has — do not fabricate.
- If nothing specific needs to be added, return empty objects: "additional_skills": {}.

DOMAIN ARCHETYPE DEFINITIONS:
- QA_AUTOMATION: test validation, defect lifecycle, CI gate enforcement, bug tracking
- BACKEND_SYSTEMS: API contracts, data persistence, concurrency, latency, service architecture  
- FULL_STACK_WEB: component delivery, client-server sync, state management, web platforms
- DATA_ML: pipelines, schema design, model evaluation, throughput, feature engineering
- CLOUD_DEVOPS: infra provisioning, deployment reliability, observability, IaC
- FRONTEND_UI: component architecture, rendering performance, user interaction flows

VIABILITY RULES:
- viable=false if estimated_ceiling_score < 65
- viable=false if 4+ required core stack items have zero transferable paradigm
- Otherwise viable=true even with partial stack gaps

STACK BRIDGE RULES:
For each technology in the JD that the candidate does NOT have, map it to the closest 
architectural paradigm the candidate CAN demonstrate:
- C# / .NET  → "interface-driven service contracts with strict type enforcement"
- Angular    → "reactive component lifecycle management and data-binding architectures"
- Vue.js     → "reactive state composition and single-file component delivery"
- Flask      → "lightweight WSGI routing and blueprint-modular API surface design"
- GCP        → "managed cloud infrastructure orchestration and serverless execution"
- Xamarin    → "shared-codebase mobile delivery with platform-abstracted UI rendering"
- React Native → "cross-platform component trees with native bridge abstraction"
Only include bridges for technologies actually missing from the candidate's profile.
"""

def run_pass1_analysis(client: Anthropic, base_resume: dict, jd_text: str) -> dict:
    """Analyzes JD and candidate data. Returns structured analysis object."""

    project_pool = [
        {"id": p["id"], "title": p["title"], "tech": p["tech"], "domain_tags": p["domain_tags"]}
        for p in base_resume.get("projects", [])
    ]

    user_content = f"""
--- TARGET JOB DESCRIPTION ---
{jd_text}

--- CANDIDATE MASTER SKILLS INVENTORY ---
{json.dumps(base_resume.get("skills_inventory", {}), indent=2)}

--- CANDIDATE PROJECT POOL (select best 3) ---
{json.dumps(project_pool, indent=2)}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        temperature=0.0,
        system=PASS1_SYSTEM,
        messages=[{"role": "user", "content": user_content}]
    )

    raw = response.content[0].text.strip()
    raw = _strip_markdown(raw)

    try:
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️ Pass 1 JSON parse error: {e}")
        return {}


# ---------------------------------------------------------------------------
# PASS 2 — BULLET GENERATION
# Uses Pass 1 analysis to generate deeply tailored bullets via VOC rewrite
# ---------------------------------------------------------------------------

PASS2_SYSTEM = """You are a Deep Semantic Resume Tailoring Engine.
Your goal is to rewrite resume bullets for the candidate using a structured analysis 
of the target job description. You must achieve an 85%+ ATS match while maintaining 
100% factual integrity.

Return ONLY raw JSON — no markdown, no backticks, no preamble.

OUTPUT SCHEMA:
{
  "ats_score": integer 0-100,
  "ats_keywords_injected": ["list of exact JD keywords successfully embedded in bullets"],
  "optimized_skills_order": ["Skills category names in JD-relevance order"],
  "optimized_experience_bullets": [
    "Headstarter AI bullet 1",
    "Headstarter AI bullet 2", 
    "Headstarter AI bullet 3",
    "Headstarter AI bullet 4",
    "ZippiAI bullet 1",
    "ZippiAI bullet 2",
    "ZippiAI bullet 3"
  ],
  "optimized_project_bullets": {
    "project_id_1": ["bullet 1", "bullet 2", "bullet 3"],
    "project_id_2": ["bullet 1", "bullet 2", "bullet 3"],
    "project_id_3": ["bullet 1", "bullet 2", "bullet 3"]
  },
  "bullet_confidence": [
    {"index": "exp_0", "score": 90, "reason": "exact VOC match to JD verb"},
    {"index": "exp_1", "score": 75, "reason": "stack bridge used"}
  ]
}

=== STRICT EXECUTION RULES ===

RULE 1 - VOC REWRITE MANDATE:
For every bullet, decompose the base bullet into:
  V = action verb | O = technical object built | C = metric/outcome
Keep C (the number) IDENTICAL. Rewrite V and O using the domain's language.
Never alter metrics. Never fabricate numbers not in the base data.

RULE 2 - DOMAIN FRAME:
Every bullet must reflect the domain archetype provided. Use the top JD verbs 
as the primary verb pool. At least one JD verb (or structural equivalent) per bullet.

RULE 3 - STACK BRIDGE PROTOCOL (CRITICAL):
When the JD requires a technology the candidate lacks, express the candidate's work 
through that technology's DESIGN PARADIGM — never append it as an adjective.
FORBIDDEN: "Python-based (C#-compatible)", "React-focused", "AWS-related"
CORRECT: Use the paradigm phrases provided in the analysis object.

RULE 4 - SOFT SKILL INJECTION:
Embed each of the 3 provided soft skills into one bullet as a demonstrated behavior — 
not as an adjective. Examples:
  accountability   → "owned end-to-end execution with zero handoff gaps"
  collaboration    → "synchronized outputs across product, QA, and dev functions"
  attention to detail → "intercepted 100% of edge-case anomalies before production merge"

RULE 5 - ATS DENSITY:
At minimum 6 of the 8 provided ATS keywords must appear VERBATIM somewhere 
in the final bullet set. Exact string match — not paraphrased.

RULE 6 - BULLET DEPTH AND LENGTH:
Every bullet must be 20-28 words. Bullets under 18 words lack technical depth. Bullets over 30 words will overflow a single-page resume — hard stop.
Structure: [Past-tense verb] + [WHAT was built/done AND HOW it was done technically] + [quantified outcome].
Both the WHAT and the HOW must be present. Never pad with trailing clauses like "with zero X gaps" or "over a Y-month window" — end at the metric.
FORBIDDEN openers: "Responsible for", "Worked on", "Helped to", "Assisted with".

RULE 7 - UNIQUENESS:
No two bullets may share the same primary verb or describe the same type of action.
Each bullet must demonstrate a DIFFERENT engineering capability from this set:
build, test, optimize, integrate, automate, architect, deploy, document, collaborate, analyze.

RULE 8 - ENTITY INTEGRITY:
Never alter company names (Headstarter AI, ZippiAI Inc.) or project titles.
Never change employment dates or project tech stack labels.

RULE 9 - METRIC INTEGRITY:
Never alter, round, or infer any numeric value not in the base resume.
If no metric exists for a bullet, omit the number — do not fabricate one.

RULE 10 - NO MARKDOWN IN VALUES:
No bold, italics, em-dashes, en-dashes inside string values.
Use only standard hyphens (-) and standard punctuation.

ATS SCORING FORMULA — compute honestly, do not optimize toward a high number:
  Start at 100
  -8 for each of the 8 required ATS keywords NOT appearing verbatim in any bullet
  -5 for any bullet that opens with a forbidden opener (RULE 6)
  -3 for any bullet exceeding 20 words
  -10 if domain archetype is not the primary lens in 60%+ of bullets
  -10 if fewer than 2 of the 3 soft skills are embedded as demonstrated behaviors
  Report the computed integer. A score of 72 that is accurate is better than 87 that is not.
  Never report above 90 unless every keyword hit and every rule passes.
"""

def run_pass2_generation(client: Anthropic, base_resume: dict, analysis: dict, force_keywords: list = None) -> dict:
    """Generates tailored bullets using Pass 1 analysis as the governing frame."""

    # Pull only selected projects from the full pool
    selected_ids = analysis.get("selected_project_ids", [])
    selected_projects = [
        p for p in base_resume.get("projects", [])
        if p["id"] in selected_ids
    ]
    # Preserve relevance ranking order
    selected_projects.sort(key=lambda p: selected_ids.index(p["id"]) if p["id"] in selected_ids else 99)

    force_block = ""
    if force_keywords:
        force_block = (
            f"\n⚠️  CRITICAL RETRY INSTRUCTION — previous attempt missed keywords. "
            f"You MUST embed each of these VERBATIM into a bullet. This overrides all other constraints:\n"
            f"{', '.join(force_keywords)}\n"
        )

    user_content = f"""{force_block}
--- PASS 1 ANALYSIS (your governing frame) ---
{json.dumps(analysis, indent=2)}

--- BASE EXPERIENCE BULLETS (rewrite these) ---
{json.dumps(base_resume.get("experience", []), indent=2)}

--- SELECTED PROJECT BULLETS (rewrite these — 3 bullets per project) ---
{json.dumps(selected_projects, indent=2)}

Target company: {analysis.get("company_name", "Target Company")}
Target role: {analysis.get("job_title", "Software Engineer")}
Domain: {analysis.get("domain_archetype", "BACKEND_SYSTEMS")}
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        temperature=0.1,
        system=PASS2_SYSTEM,
        messages=[{"role": "user", "content": user_content}]
    )

    raw = response.content[0].text.strip()
    raw = _strip_markdown(raw)

    try:
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️ Pass 2 JSON parse error: {e}")
        return {}


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT — called by app.py
# ---------------------------------------------------------------------------

def generate_tailored_resume_content(client: Anthropic, base_resume: dict, jd_text: str) -> dict:
    """
    Full two-pass pipeline. Returns merged result dict for LaTeX builder.
    Checks cache first — skips API calls if JD was previously processed.
    """

    # Cache check
    cached = _load_from_cache(jd_text)
    if cached:
        return cached

    # Pass 1 — Analysis
    print("🔍 Pass 1: Analyzing JD — domain classification, keyword extraction, project selection...")
    analysis = run_pass1_analysis(client, base_resume, jd_text)

    if not analysis:
        print("❌ Pass 1 failed — could not parse analysis object.")
        return {}

    # Viability gate
    viable = analysis.get("viable", True)
    ceiling = analysis.get("estimated_ceiling_score", 100)
    if not viable or ceiling < 65:
        reason = analysis.get("rejection_reason", "Stack mismatch too severe.")
        print(f"\n⚠️  VIABILITY WARNING")
        print(f"   Estimated ceiling ATS score: {ceiling}/100")
        print(f"   Reason: {reason}")
        confirm = input("\n   Proceed anyway? This resume may not clear ATS filters. (y/n): ").strip().lower()
        if confirm != "y":
            print("❌ Application aborted by user.")
            return {}

    # Pass 2 — Generation
    print("✍️  Pass 2: Generating tailored bullets via VOC rewrite and stack bridging...")
    generation = run_pass2_generation(client, base_resume, analysis)

    if not generation:
        print("❌ Pass 2 failed — could not parse generation object.")
        return {}

    # Retry only if score is below 75 AND there are specific missing keywords to force in
    ats_score = generation.get("ats_score", 0)
    if ats_score < 75:
        injected = set(generation.get("ats_keywords_injected", []))
        required = set(analysis.get("ats_keywords", []))
        missing = list(required - injected)
        if missing:
            print(f"⚠️  ATS score {ats_score}/100 — retrying Pass 2 to force missing keywords: {', '.join(missing)}")
            retry = run_pass2_generation(client, base_resume, analysis, force_keywords=missing)
            if retry and retry.get("ats_score", 0) > ats_score:
                print(f"✅ Retry improved score: {ats_score} → {retry.get('ats_score')}/100")
                generation = retry
            else:
                print(f"⚠️  Retry did not improve score — keeping original result.")
        else:
            print(f"⚠️  ATS score {ats_score}/100 — all keywords injected but structural rules penalized. Score reflects honest evaluation.")

    # Merge Pass 1 + Pass 2 into single result
    result = {**analysis, **generation}

    # Save to cache
    _save_to_cache(jd_text, result)

    # Print confidence summary
    _print_confidence_summary(generation.get("bullet_confidence", []))

    return result


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """Strips ```json fences if model wraps output despite instructions."""
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
        return "\n".join(lines).strip()
    return text

def _print_confidence_summary(bullet_confidence: list):
    """Prints a readable summary of bullet confidence scores to terminal."""
    if not bullet_confidence:
        return
    print("\n📊 Bullet Confidence Summary:")
    for b in bullet_confidence:
        score = b.get("score", 0)
        icon = "✅" if score >= 80 else "⚠️ " if score >= 65 else "❌"
        print(f"   {icon} [{b.get('index', '?')}] {score}/100 — {b.get('reason', '')}")
    avg = sum(b.get("score", 0) for b in bullet_confidence) / len(bullet_confidence)
    print(f"\n   Average bullet confidence: {avg:.0f}/100")