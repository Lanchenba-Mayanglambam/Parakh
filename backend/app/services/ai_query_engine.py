import re
import time
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from app.core.config import settings
from app.db.models import Project, RiskScore, DuplicateCandidate, ProgressRecord, FinancialRecord

logger = logging.getLogger("ai_query_engine")

SYSTEM_INSTRUCTION = """You are PARAKH AI, the official intelligent assistant for the Members of Parliament Local Area Development Scheme (MPLADS) monitoring & vigilance platform.

CRITICAL OPERATIONAL RULES (MANDATORY COMPLIANCE):
1. PROJECT-RELATED QUESTIONS ONLY:
   - You must exclusively answer inquiries related to MPLADS works, government projects, fund expenditures, allocations, Member of Parliament (MP) development records, district implementations, execution delays, and risk anomalies.
   - If the user asks about unrelated topics (e.g. general knowledge, entertainment, sports, coding, cooking, personal opinions, or politics outside of MPLADS works), immediately and politely decline with:
     "I am dedicated exclusively to MPLADS project vigilance, expenditure tracking, and anomaly detection. I cannot assist with unrelated topics."

2. ZERO HALLUCINATION & STRICT GROUNDING:
   - You must answer ONLY using the verified database records and statistics provided in the context below.
   - NEVER make up, guess, or fabricate project titles, numbers, budget figures, dates, contractor names, or progress percentages.

3. UNAVAILABLE DATA:
   - If the user asks for a project, person, district, or detail that is NOT found in the provided database context, you must state clearly and directly:
     "I do not have the data for that inquiry in the current official MPLADS database."
   - Do NOT try to invent plausible-sounding details or assume numbers.

4. ACCURACY & FORMATTING:
   - Present your answer using clean GitHub-flavored Markdown with clear headings (###), bullet points, and bold key metrics.
   - State figures accurately (e.g., in Lakhs or Crores as provided).
"""


class ControlledAIQueryEngine:
    """
    Intelligent Natural Language Conversational Analytics & Vigilance Assistant for MPLADS.
    Powered by Google Gemini AI with strict grounding against the 95,964 authentic MoSPI records.
    Guarantees zero hallucination and project-only scope.
    """

    def __init__(self, db: Session):
        self.db = db

    def _call_gemini_llm(self, user_query: str, db_context: str) -> Optional[str]:
        """Call Google Gemini API with strict system grounding and temperature 0.1 to eliminate hallucination."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return None

        model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt = (
            f"=== VERIFIED MPLADS DATABASE CONTEXT ===\n"
            f"{db_context}\n"
            f"=========================================\n\n"
            f"User Question: {user_query}\n\n"
            f"Instructions: Answer the user's question using ONLY the verified database context above. "
            f"If the information is not available in the context, respond that you do not have the data. "
            f"If the question is unrelated to MPLADS projects, decline politely."
        )

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for strict factual accuracy
                "maxOutputTokens": 1024,
            }
        }

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"]
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")

        return None

    def process_query(self, query: str, context_project_id: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        q_raw = query.strip()
        q = q_raw.lower()

        matched_projects = []
        structured_data = {}
        suggested_followups = []
        interpretation = ""
        answer_md = ""

        # Clean words from query
        words = set(re.findall(r'\b\w+\b', q))

        # Check for Project ID in query (e.g. MPLAD-77000, MPLAD-8386, etc.)
        project_id_match = re.search(r'(mplad-[a-z0-9\-]+|ws\/[a-z0-9\-\/]+)', q)
        target_pid = project_id_match.group(1).upper() if project_id_match else (context_project_id.upper() if context_project_id else None)

        # -------------------------------------------------------------
        # 0. GREETINGS & CAPABILITY OVERVIEW
        # -------------------------------------------------------------
        greeting_words = {"hi", "hello", "hey", "namaste", "greetings", "morning", "afternoon", "evening", "hola"}
        is_pure_greeting = (len(words) <= 3 and any(w in greeting_words for w in words)) or q in ["hi", "hello", "hey", "hello there", "good morning", "good evening", "namaste"]
        is_persona_query = any(p in q for p in ["who are you", "what can you do", "what are you", "how can you help", "how to use", "what is your purpose", "introduce yourself"])
        is_gratitude = any(p in q for p in ["thank you", "thanks", "great job", "awesome", "perfect", "good bye", "bye", "see you"])

        if is_pure_greeting or is_persona_query:
            interpretation = "Conversational greeting and AI assistant capability overview"
            total_projects = self.db.query(func.count(Project.project_id)).scalar() or 0
            total_exp = round((self.db.query(func.sum(Project.expenditure)).scalar() or 0.0) / 100.0, 2)

            answer_md = "### 👋 Hello! I am **PARAKH AI**, your **MPLADS Project Vigilance & Intelligence Assistant**\n\n"
            answer_md += f"I am connected in real time to the official repository of **{total_projects:,} authentic government works** and **₹{total_exp:,.2f} Crores in capital expenditure** across India.\n\n"
            answer_md += "#### 💡 How I Can Assist You:\n"
            answer_md += "1. **🔍 Specific Project Audits:** Ask about any project ID (e.g. *'Tell me about MPLAD-77000'* or *'Status of MPLAD-15402'*).\n"
            answer_md += "2. **🏛️ Member of Parliament Works:** Ask about works recommended by an MP (e.g., *'Works by Janardan Mishra'* or *'Devusinh Chauhan'*).\n"
            answer_md += "3. **📍 State & District Telemetry:** Ask *'Show projects in Thoubal, Manipur'* or *'High risk works in Uttar Pradesh'*.\n"
            answer_md += "4. **💰 Expenditure & Anomaly Analysis:** Ask *'Find projects with high cost overruns'* or *'Top spending states'*.\n"
            answer_md += "5. **👥 Duplicate Work Checks:** Ask *'Are there duplicate projects within 500m?'*\n\n"
            answer_md += "> *Note: I only answer questions related to MPLADS projects and verified government records. If data is not available, I will inform you directly without guessing.*"

            sample_projects = self.db.query(Project).join(RiskScore).order_by(desc(RiskScore.overall_score)).limit(3).all()
            for p in sample_projects:
                matched_projects.append(self._format_card(p))

            suggested_followups = [
                "Tell me about project MPLAD-77000",
                "Show works by Janardan Mishra",
                "Top 5 states by total expenditure",
                "Show critical risk projects nationwide"
            ]

        elif is_gratitude:
            interpretation = "Acknowledging user feedback"
            answer_md = "### You're very welcome! 😊\n\n"
            answer_md += "I am here to assist you with authentic MPLADS project audits, expenditure records, and anomaly tracking.\n\n"
            answer_md += "Feel free to ask about any project ID, district, or Member of Parliament!"
            suggested_followups = [
                "Tell me about project MPLAD-77000",
                "Top 5 states by total expenditure",
                "Show critical risk projects nationwide"
            ]

        # -------------------------------------------------------------
        # 1. SPECIFIC PROJECT ID INQUIRY
        # -------------------------------------------------------------
        elif target_pid:
            interpretation = f"Auditing specific project record '{target_pid}'"
            p = self.db.query(Project).filter(Project.project_id.ilike(target_pid)).first()

            if not p:
                # ZERO HALLUCINATION: Clearly state data is not available
                answer_md = f"### ⚠️ Project Not Found\n\n"
                answer_md += f"I do not have the data for project **`{target_pid}`** in the official MPLADS database.\n\n"
                answer_md += "Please verify the project ID format (e.g., `MPLAD-77000`) or search by district and MP name."
                suggested_followups = [
                    "Search project by description",
                    "Show critical risk projects in Manipur",
                    "Show overview of all projects"
                ]
            else:
                matched_projects.append(self._format_card(p))
                r = p.risk_score
                reasons = json.loads(r.reasons_json) if r and r.reasons_json else []

                # Fetch recent financial transactions
                txs = self.db.query(FinancialRecord).filter(FinancialRecord.project_id == p.project_id).order_by(desc(FinancialRecord.date)).limit(5).all()
                tx_lines = [f"- {t.date.strftime('%Y-%m-%d') if hasattr(t.date, 'strftime') else t.date}: ₹{t.amount:.2f}L ({t.record_type}) to '{t.vendor_or_payee}'" for t in txs]
                tx_context = "\n".join(tx_lines) if tx_lines else "No transaction vouchers recorded."

                # Fetch duplicate candidate link
                dup = self.db.query(DuplicateCandidate).filter(or_(DuplicateCandidate.project_a_id == p.project_id, DuplicateCandidate.project_b_id == p.project_id)).first()
                dup_context = f"Flagged as duplicate of {dup.project_b_id if dup.project_a_id == p.project_id else dup.project_a_id} with similarity score {dup.duplicate_score}/100" if dup else "No duplicate flag."

                db_context = f"""
Project ID: {p.project_id}
Description: {p.description}
State: {p.state}
District: {p.district}
Constituency: {p.constituency}
GPS Coordinates: {p.latitude:.5f}° N, {p.longitude:.5f}° E
MP: {p.mp_id}
Implementing Agency: {p.implementing_agency}
Sanctioned Amount: ₹{p.sanctioned_amount:.2f} Lakhs
Released Amount: ₹{p.released_amount:.2f} Lakhs
Expenditure: ₹{p.expenditure:.2f} Lakhs
Physical Progress: {p.physical_progress:.1f}%
Financial Progress: {p.financial_progress:.1f}%
Status: {p.status}
Risk Level: {r.risk_level if r else 'LOW'} (Score: {r.overall_score if r else 0:.0f}/100)
Risk Factors: {', '.join(reasons) if reasons else 'Normal progress, no red flags'}
Duplicate Status: {dup_context}
Recent Financial Vouchers:
{tx_context}
"""
                # Call Gemini LLM with verified DB context
                llm_response = self._call_gemini_llm(q_raw, db_context)
                if llm_response:
                    answer_md = llm_response
                else:
                    # Deterministic factual fallback if API is unreachable
                    answer_md = f"### 📋 Project Audit: **{p.project_id}**\n\n"
                    answer_md += f"**Description:** {p.description}\n\n"
                    answer_md += f"- **Location:** {p.district}, {p.state} ({p.constituency})\n"
                    answer_md += f"- **Exact GPS:** `{p.latitude:.5f}° N, {p.longitude:.5f}° E`\n"
                    answer_md += f"- **Recommending MP:** {p.mp_id}\n"
                    answer_md += f"- **Agency:** {p.implementing_agency}\n\n"
                    answer_md += "#### 💰 Financial & Physical Status:\n"
                    answer_md += f"- **Sanctioned:** ₹{p.sanctioned_amount:.2f} Lakhs\n"
                    answer_md += f"- **Expended:** ₹{p.expenditure:.2f} Lakhs ({p.financial_progress:.0f}%)\n"
                    answer_md += f"- **Physical Progress:** `{p.physical_progress:.0f}%` &bull; **Status:** `{p.status}`\n"
                    answer_md += f"- **Risk Rating:** **`{r.risk_level if r else 'LOW'}`** ({r.overall_score if r else 0:.0f}/100)\n"
                    if reasons:
                        answer_md += f"- **Key Risk Driver:** {reasons[0]}\n"

                suggested_followups = [
                    f"Show transactions for {p.project_id}",
                    f"Show nearby projects around {p.district}",
                    f"Show all works by {p.mp_id}"
                ]

        # -------------------------------------------------------------
        # 2. MEMBER OF PARLIAMENT (MP) INQUIRY
        # -------------------------------------------------------------
        elif self._is_mp_query(q):
            mp_name = self._extract_mp_name(q) or q_raw
            interpretation = f"Retrieving MPLADS development record for MP '{mp_name}'"

            projects = self.db.query(Project).outerjoin(RiskScore).filter(Project.mp_id.ilike(f"%{mp_name}%")).all()

            if not projects:
                answer_md = f"### ⚠️ No Records Found\n\n"
                answer_md += f"I do not have data for Member of Parliament **'{mp_name}'** in the official MPLADS records.\n\n"
                answer_md += "Please verify the spelling or try searching for another MP (e.g. *'Janardan Mishra'*, *'Devusinh Chauhan'*, *'Aparajita Sarangi'*)."
                suggested_followups = [
                    "Show works by Janardan Mishra",
                    "Show works by Devusinh Chauhan",
                    "Top 5 states by total expenditure"
                ]
            else:
                total_cnt = len(projects)
                total_sanc = sum(p.sanctioned_amount for p in projects)
                total_spent = sum(p.expenditure for p in projects)
                crit_cnt = sum(1 for p in projects if p.risk_score and p.risk_score.risk_level == "CRITICAL")
                high_cnt = sum(1 for p in projects if p.risk_score and p.risk_score.risk_level == "HIGH")

                sample_list = []
                for p in projects[:6]:
                    matched_projects.append(self._format_card(p))
                    sample_list.append(f"- {p.project_id} ({p.district}, {p.state}): '{p.description[:60]}...' | Spent: ₹{p.expenditure:.1f}L | Phys: {p.physical_progress:.0f}% | Risk: {p.risk_score.risk_level if p.risk_score else 'LOW'}")

                db_context = f"""
MP Name: {projects[0].mp_id}
Total Works Recommended: {total_cnt}
Total Sanctioned Capital: ₹{total_sanc:.2f} Lakhs (₹{total_sanc/100:.2f} Crores)
Total Expenditure: ₹{total_spent:.2f} Lakhs (₹{total_spent/100:.2f} Crores)
Fund Utilization: {(total_spent / max(1.0, total_sanc)) * 100:.1f}%
Risk Profile: {crit_cnt} Critical Risk, {high_cnt} High Risk, {total_cnt - crit_cnt - high_cnt} Normal
Primary Districts: {', '.join(list(set(p.district for p in projects))[:5])}
Sample Works:
{chr(10).join(sample_list)}
"""
                llm_response = self._call_gemini_llm(q_raw, db_context)
                if llm_response:
                    answer_md = llm_response
                else:
                    answer_md = f"### 🏛️ MP Record: **{projects[0].mp_id}**\n\n"
                    answer_md += f"- **Total Works:** **`{total_cnt}`** projects\n"
                    answer_md += f"- **Sanctioned Amount:** **₹{total_sanc/100:.2f} Crores** (₹{total_sanc:,.1f} Lakhs)\n"
                    answer_md += f"- **Total Expenditure:** **₹{total_spent/100:.2f} Crores**\n"
                    answer_md += f"- **Utilization Rate:** **{(total_spent / max(1.0, total_sanc)) * 100:.1f}%**\n"
                    answer_md += f"- **Vigilance Alert:** {crit_cnt} Critical risk projects flagged.\n"

                suggested_followups = [
                    f"Show critical works by {projects[0].mp_id}",
                    f"Show expenditure timeline for {projects[0].mp_id}",
                    "Top spending MPs nationwide"
                ]

        # -------------------------------------------------------------
        # 3. LOCATION QUERY (STATE / DISTRICT)
        # -------------------------------------------------------------
        elif self._detect_location(q):
            loc = self._detect_location(q)
            interpretation = f"Filtering MPLADS works in location '{loc.title()}'"

            projects = (
                self.db.query(Project)
                .outerjoin(RiskScore)
                .filter(or_(Project.state.ilike(f"%{loc}%"), Project.district.ilike(f"%{loc}%")))
                .order_by(desc(RiskScore.overall_score))
                .all()
            )

            if not projects:
                answer_md = f"### ⚠️ No Location Data Found\n\n"
                answer_md += f"I do not have project records for **'{loc.title()}'** in the official MPLADS database."
            else:
                total_cnt = len(projects)
                total_sanc = sum(p.sanctioned_amount for p in projects)
                total_spent = sum(p.expenditure for p in projects)
                crit_cnt = sum(1 for p in projects if p.risk_score and p.risk_score.risk_level == "CRITICAL")

                sample_list = []
                for p in projects[:6]:
                    matched_projects.append(self._format_card(p))
                    sample_list.append(f"- {p.project_id} ({p.district}): '{p.description[:55]}...' | Spent: ₹{p.expenditure:.1f}L | Phys: {p.physical_progress:.0f}% | Risk: {p.risk_score.risk_level if p.risk_score else 'LOW'}")

                db_context = f"""
Location: {loc.title()}
Total Projects: {total_cnt}
Total Sanctioned Capital: ₹{total_sanc/100:.2f} Crores
Total Expenditure: ₹{total_spent/100:.2f} Crores
Utilization Rate: {(total_spent / max(1.0, total_sanc)) * 100:.1f}%
Critical Risk Projects Flagged: {crit_cnt}
Sample High-Priority Projects:
{chr(10).join(sample_list)}
"""
                llm_response = self._call_gemini_llm(q_raw, db_context)
                if llm_response:
                    answer_md = llm_response
                else:
                    answer_md = f"### 📍 MPLADS Intelligence: **{loc.title()}**\n\n"
                    answer_md += f"- **Total Works:** **`{total_cnt:,}`** projects\n"
                    answer_md += f"- **Total Sanctioned:** **₹{total_sanc/100:.2f} Crores**\n"
                    answer_md += f"- **Total Expended:** **₹{total_spent/100:.2f} Crores** ({(total_spent / max(1.0, total_sanc)) * 100:.1f}%)\n"
                    answer_md += f"- **Critical Risk Alerts:** `{crit_cnt}` projects\n"

                suggested_followups = [
                    f"Show critical risk works in {loc.title()}",
                    f"Show delayed works in {loc.title()}",
                    "Top 5 states by total expenditure"
                ]

        # -------------------------------------------------------------
        # 4. MACRO / DATASET OVERVIEW / AGGREGATE STATS
        # -------------------------------------------------------------
        elif any(k in q for k in ["dataset", "database", "total expenditure", "top states", "statistics", "how many projects", "overview", "provenance"]):
            interpretation = "Aggregating national MPLADS dataset metrics"
            total_projects = self.db.query(func.count(Project.project_id)).scalar() or 0
            total_expenditure = self.db.query(func.sum(Project.expenditure)).scalar() or 0.0
            total_sanctioned = self.db.query(func.sum(Project.sanctioned_amount)).scalar() or 0.0
            crit_count = self.db.query(func.count(RiskScore.id)).filter(RiskScore.risk_level == "CRITICAL").scalar() or 0
            high_count = self.db.query(func.count(RiskScore.id)).filter(RiskScore.risk_level == "HIGH").scalar() or 0
            dup_count = self.db.query(func.count(DuplicateCandidate.id)).scalar() or 0

            top_states = (
                self.db.query(Project.state, func.count(Project.project_id), func.sum(Project.expenditure))
                .group_by(Project.state)
                .order_by(desc(func.sum(Project.expenditure)))
                .limit(5)
                .all()
            )
            top_states_str = "\n".join([f"- {st}: {cnt:,} projects, ₹{(exp or 0)/100:.2f} Cr" for st, cnt, exp in top_states])

            db_context = f"""
Dataset: National Official MPLADS Repository (MoSPI)
Total Authentic Projects: {total_projects:,}
Total Sanctioned: ₹{total_sanctioned/100:.2f} Crores
Total Expenditure: ₹{total_expenditure/100:.2f} Crores
Fund Utilization Rate: {(total_expenditure / max(1.0, total_sanctioned)) * 100:.1f}%
Risk Breakdown:
- Critical Risk Projects: {crit_count:,}
- High Risk Projects: {high_count:,}
- Duplicate Candidates Flagged: {dup_count}
Top 5 States by Capital Expenditure:
{top_states_str}
"""
            llm_response = self._call_gemini_llm(q_raw, db_context)
            if llm_response:
                answer_md = llm_response
            else:
                answer_md = f"### 📊 National MPLADS Intelligence Overview\n\n"
                answer_md += f"- **Total Projects:** **`{total_projects:,}`** authentic government works\n"
                answer_md += f"- **Total Sanctioned:** **₹{total_sanctioned/100:,.2f} Crores**\n"
                answer_md += f"- **Total Expended:** **₹{total_expenditure/100:,.2f} Crores**\n"
                answer_md += f"- **Fund Utilization:** **{(total_expenditure / max(1.0, total_sanctioned)) * 100:.1f}%**\n"
                answer_md += f"- **Risk Alerts:** `{crit_count:,}` Critical & `{high_count:,}` High Risk works\n"
                answer_md += f"- **Duplicates Flagged:** `{dup_count}` suspicious double-billed candidates\n"

            suggested_followups = [
                "Show critical risk projects nationwide",
                "Show works by Janardan Mishra",
                "Top 5 states by total expenditure"
            ]

        # -------------------------------------------------------------
        # 5. GENERAL FREE-TEXT SEARCH WITH STRICT ANTI-HALLUCINATION
        # -------------------------------------------------------------
        else:
            interpretation = f"Semantic search for '{q_raw}' in MPLADS dataset"
            terms = [t for t in re.split(r'\s+', q) if len(t) > 2 and t not in ["show", "find", "what", "which", "list", "give", "the", "and", "for", "with", "project", "projects", "tell", "about", "is"]]

            projects = []
            if terms:
                filters = []
                for t in terms:
                    filters.append(Project.description.ilike(f"%{t}%"))
                    filters.append(Project.district.ilike(f"%{t}%"))
                    filters.append(Project.constituency.ilike(f"%{t}%"))
                    filters.append(Project.state.ilike(f"%{t}%"))
                    filters.append(Project.implementing_agency.ilike(f"%{t}%"))
                    filters.append(Project.mp_id.ilike(f"%{t}%"))

                projects = (
                    self.db.query(Project)
                    .outerjoin(RiskScore)
                    .filter(or_(*filters))
                    .order_by(desc(RiskScore.overall_score))
                    .limit(5)
                    .all()
                )

            if not projects:
                # Check with Gemini to see if it's off-topic or simply missing data
                db_context = "No matching projects, MPs, or records found in the official MPLADS database."
                llm_response = self._call_gemini_llm(q_raw, db_context)
                if llm_response:
                    answer_md = llm_response
                else:
                    answer_md = f"### ⚠️ Data Not Found\n\n"
                    answer_md += f"I do not have the data for **'{q_raw}'** in the official MPLADS database.\n\n"
                    answer_md += "Please verify the search query or search by a valid Project ID (e.g. `MPLAD-77000`), Member of Parliament, or District."
            else:
                sample_list = []
                for p in projects:
                    matched_projects.append(self._format_card(p))
                    r = p.risk_score
                    reasons = json.loads(r.reasons_json) if r and r.reasons_json else []
                    top_reason = reasons[0] if reasons else f"Risk Score: {r.overall_score if r else 0:.0f}/100"
                    sample_list.append(f"- ID: {p.project_id} | Location: {p.district}, {p.state} | Desc: '{p.description[:60]}...' | Spent: ₹{p.expenditure:.1f}L | Risk: {r.risk_level if r else 'LOW'} | Reason: {top_reason}")

                db_context = f"""
Search Query: {q_raw}
Matched Projects Count: {len(projects)}
Matching Project Records:
{chr(10).join(sample_list)}
"""
                llm_response = self._call_gemini_llm(q_raw, db_context)
                if llm_response:
                    answer_md = llm_response
                else:
                    answer_md = f"### Search Results for **'{q_raw}'**\n\n"
                    answer_md += f"Found **{len(projects)}** matching authentic project records:\n\n"
                    for p in projects:
                        r = p.risk_score
                        answer_md += f"- **{p.project_id}** ({p.district}, {p.state}): `{r.risk_level if r else 'LOW'}` &bull; *{p.description[:65]}...*\n"

            suggested_followups = [
                "Show critical risk projects nationwide",
                "Top 5 states by total expenditure",
                "Tell me about project MPLAD-77000"
            ]

        exec_time = round((time.time() - start_time) * 1000, 1)

        return {
            "query": query,
            "interpretation": interpretation,
            "answer_markdown": answer_md,
            "structured_data": structured_data,
            "matched_projects": matched_projects,
            "suggested_followups": suggested_followups,
            "execution_time_ms": exec_time
        }

    def _is_mp_query(self, q: str) -> bool:
        """Check if query is asking about an MP."""
        if any(k in q for k in ["mp ", "member of parliament", "mps", "hon'ble", "who is", "works by", "projects by", "spending mp"]):
            return True
        mp_name = self._extract_mp_name(q)
        return mp_name is not None

    def _extract_mp_name(self, q: str) -> Optional[str]:
        """Check if any MP name exists in query text."""
        known_mps = [
            "janardan mishra", "devusinh", "devusinh jesingbhai", "aparajita", "aparajita sarangi",
            "anita nagarsingh", "ajay bhatt", "chandra sekhar", "manoj tiwari", "hema malini",
            "kiren rijiju", "nitin gadkari", "rajnath singh", "dharmendra pradhan", "anurag thakur",
            "shashi tharoor", "supriya sule", "giriraj singh", "piyush goyal", "nirmala sitharaman"
        ]
        for m in known_mps:
            if m in q:
                return m

        tokens = [t for t in re.split(r'\s+', q) if len(t) > 3 and t not in ["show", "tell", "about", "works", "projects", "what", "which", "where", "who", "is"]]
        for t in tokens:
            match = self.db.query(Project.mp_id).filter(Project.mp_id.ilike(f"%{t}%")).first()
            if match:
                return t
        return None

    def _detect_location(self, q: str) -> Optional[str]:
        """Detect any Indian state, district, or prominent city from text."""
        locations = [
            "uttar pradesh", "bihar", "maharashtra", "west bengal", "madhya pradesh",
            "tamil nadu", "rajasthan", "karnataka", "gujarat", "andhra pradesh",
            "odisha", "telangana", "kerala", "jharkhand", "assam", "punjab",
            "chhattisgarh", "haryana", "delhi", "jammu and kashmir", "uttarakhand",
            "himachal pradesh", "tripura", "meghalaya", "manipur", "nagaland",
            "goa", "arunachal pradesh", "mizoram", "sikkim", "puducherry",
            "chandigarh", "ladakh", "rewa", "kheda", "bhubaneswar", "gorakhpur",
            "varanasi", "amritsar", "jaunpur", "bijnor", "lucknow", "patna", "jaipur", "thoubal"
        ]
        for s in locations:
            if s in q:
                return s
        return None

    def _format_card(self, p: Project) -> Dict[str, Any]:
        risk = p.risk_score
        reasons = json.loads(risk.reasons_json) if risk and risk.reasons_json else []
        return {
            "project_id": p.project_id,
            "state": p.state,
            "district": p.district,
            "project_type": p.project_type,
            "description": p.description,
            "estimated_cost": p.estimated_cost,
            "expenditure": p.expenditure,
            "physical_progress": p.physical_progress,
            "financial_progress": p.financial_progress,
            "risk_level": risk.risk_level if risk else "LOW",
            "overall_score": risk.overall_score if risk else 0.0,
            "key_reasons": reasons[:3]
        }
