import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from app.db.session import get_db
from app.db.models import (
    Project, RiskScore, Alert, FinancialRecord, ProgressRecord,
    DuplicateCandidate, User
)
from app.core.auth import get_current_user
from app.schemas.project import (
    ProjectOut, ProjectDetailOut, FinancialRecordOut,
    ProjectAdminUpdate, InvestigationReportCreate, AnalystVerificationCreate
)
from app.services.ml.duplicate_detector import haversine_distance_km


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    constituency: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    agency: Optional[str] = Query(None),
    mp_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_cost_escalation: Optional[float] = Query(None),
    min_delay_days: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("risk_desc"),  # risk_desc, cost_desc, delay_desc, newest
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Project).outerjoin(RiskScore)

    if state:
        query = query.filter(Project.state.ilike(f"%{state}%"))
    if district:
        query = query.filter(Project.district.ilike(f"%{district}%"))
    if constituency:
        query = query.filter(Project.constituency.ilike(f"%{constituency}%"))
    if project_type:
        query = query.filter(Project.project_type.ilike(f"%{project_type}%"))
    if risk_level:
        query = query.filter(RiskScore.risk_level == risk_level.upper())
    if status:
        query = query.filter(Project.status == status.upper())
    if agency:
        query = query.filter(Project.implementing_agency.ilike(f"%{agency}%"))
    if mp_name:
        query = query.filter(Project.mp_id.ilike(f"%{mp_name}%"))
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Project.project_id.ilike(s),
                Project.description.ilike(s),
                Project.district.ilike(s),
                Project.constituency.ilike(s),
                Project.mp_id.ilike(s),
                Project.implementing_agency.ilike(s)
            )
        )


    # Sorting
    if sort_by == "risk_desc":
        query = query.order_by(RiskScore.overall_score.desc().nullslast())
    elif sort_by == "cost_desc":
        query = query.order_by(Project.expenditure.desc())
    elif sort_by == "newest":
        query = query.order_by(Project.created_at.desc())
    else:
        query = query.order_by(RiskScore.overall_score.desc().nullslast())

    projects = query.offset(offset).limit(limit).all()

    now = datetime.now(timezone.utc)
    results = []
    for p in projects:
        cost_esc = max(0.0, ((p.expenditure - p.sanctioned_amount) / max(1.0, p.sanctioned_amount)) * 100.0)
        delay = 0
        if p.expected_completion_date and p.status != "COMPLETED" and p.physical_progress < 100.0:
            exp_d = p.expected_completion_date.replace(tzinfo=timezone.utc) if p.expected_completion_date.tzinfo is None else p.expected_completion_date
            if now > exp_d:
                delay = (now - exp_d).days

        if min_cost_escalation is not None and cost_esc < min_cost_escalation:
            continue
        if min_delay_days is not None and delay < min_delay_days:
            continue

        p_out = ProjectOut.model_validate(p)
        p_out.cost_escalation_pct = round(cost_esc, 1)
        p_out.delay_days = delay
        p_out.progress_gap_pct = round(p.financial_progress - p.physical_progress, 1)
        p_out.alerts_count = len(p.alerts) if p.alerts else 0
        results.append(p_out)

    return results


@router.get("/gis/markers")
def get_gis_markers(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    project_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, le=100000),
    db: Session = Depends(get_db)
):
    """
    Lightweight GeoJSON / marker feed optimized for React-Leaflet GIS rendering.
    Supports full-scale retrieval, search, and state/district level 100% extraction.
    """
    base_query = db.query(
        Project.project_id,
        Project.latitude,
        Project.longitude,
        Project.state,
        Project.district,
        Project.constituency,
        Project.project_type,
        Project.mp_id,
        Project.implementing_agency,
        Project.description,
        Project.sanctioned_amount,
        Project.expenditure,
        Project.physical_progress,
        Project.financial_progress,
        Project.status,
        RiskScore.risk_level,
        RiskScore.overall_score,
        RiskScore.reasons_json
    ).join(RiskScore, Project.project_id == RiskScore.project_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        base_query = base_query.filter(
            or_(
                Project.project_id.ilike(term),
                Project.description.ilike(term),
                Project.district.ilike(term),
                Project.constituency.ilike(term),
                Project.state.ilike(term)
            )
        )
    if state and state.strip():
        base_query = base_query.filter(Project.state.ilike(f"%{state.strip()}%"))
    if district and district.strip():
        base_query = base_query.filter(Project.district.ilike(f"%{district.strip()}%"))
    if project_type and project_type.strip():
        base_query = base_query.filter(Project.project_type.ilike(f"%{project_type.strip()}%"))
    if risk_level and risk_level.strip():
        base_query = base_query.filter(RiskScore.risk_level == risk_level.strip().upper())

    # Determine effective limit
    # If filtered by state, district, or search, return ALL matching projects by default
    if state or district or search:
        effective_limit = limit or 100000
        projects_tuples = base_query.limit(effective_limit).all()
    elif limit and limit >= 50000:
        # User explicitly requested all 95k+ projects
        projects_tuples = base_query.limit(limit).all()
    else:
        # Balanced Pan-India overview: sample pro-rata across EVERY SINGLE state (all 35 states represented)
        effective_limit = limit or 5000
        per_state = max(45, effective_limit // 35)

        where_clauses = ["1=1"]
        params = {"per_state": per_state}

        if risk_level and risk_level.strip():
            where_clauses.append("r.risk_level = :risk_level")
            params["risk_level"] = risk_level.strip().upper()
        if project_type and project_type.strip():
            where_clauses.append("p.project_type ILIKE :project_type")
            params["project_type"] = f"%{project_type.strip()}%"

        where_sql = " AND ".join(where_clauses)
        sql = text(f"""
            WITH ranked AS (
                SELECT p.project_id, p.latitude, p.longitude, p.state, p.district, p.constituency,
                       p.project_type, p.mp_id, p.implementing_agency, p.description,
                       p.sanctioned_amount, p.expenditure, p.physical_progress, p.financial_progress,
                       p.status, r.risk_level, r.overall_score, r.reasons_json,
                       ROW_NUMBER() OVER (PARTITION BY p.state ORDER BY r.overall_score DESC, p.project_id) as rn
                FROM projects p
                JOIN risk_scores r ON p.project_id = r.project_id
                WHERE {where_sql}
            )
            SELECT project_id, latitude, longitude, state, district, constituency,
                   project_type, mp_id, implementing_agency, description,
                   sanctioned_amount, expenditure, physical_progress, financial_progress,
                   status, risk_level, overall_score, reasons_json
            FROM ranked
            WHERE rn <= :per_state;
        """)
        projects_tuples = db.execute(sql, params).fetchall()

    # If include_id specified (e.g. initialProjectId), ensure it is present
    included_ids = {r[0].upper() for r in projects_tuples}
    if include_id and include_id.upper() not in included_ids:
        targeted = db.query(
            Project.project_id,
            Project.latitude,
            Project.longitude,
            Project.state,
            Project.district,
            Project.constituency,
            Project.project_type,
            Project.mp_id,
            Project.implementing_agency,
            Project.description,
            Project.sanctioned_amount,
            Project.expenditure,
            Project.physical_progress,
            Project.financial_progress,
            Project.status,
            RiskScore.risk_level,
            RiskScore.overall_score,
            RiskScore.reasons_json
        ).join(RiskScore, Project.project_id == RiskScore.project_id).filter(
            func.upper(Project.project_id) == include_id.upper()
        ).first()
        if targeted:
            projects_tuples.insert(0, targeted)

    markers = []
    for r in projects_tuples:
        reasons = json.loads(r[17]) if r[17] else []
        markers.append({
            "project_id": r[0],
            "latitude": r[1],
            "longitude": r[2],
            "state": r[3],
            "district": r[4],
            "constituency": r[5],
            "project_type": r[6],
            "mp_id": r[7],
            "implementing_agency": r[8],
            "description": r[9][:80] if r[9] else "",
            "sanctioned_amount": r[10],
            "expenditure": r[11],
            "physical_progress": r[12],
            "financial_progress": r[13],
            "status": r[14],
            "risk_level": r[15] if r[15] else "LOW",
            "overall_score": r[16] if r[16] else 0.0,
            "primary_reason": reasons[0] if reasons else "Normal Project"
        })

    return markers



@router.get("/filter-options")

def get_filter_options(db: Session = Depends(get_db)):
    states = [s[0] for s in db.query(Project.state).distinct().order_by(Project.state).all() if s[0]]
    project_types = [t[0] for t in db.query(Project.project_type).distinct().order_by(Project.project_type).all() if t[0]]
    statuses = ["SANCTIONED", "IN_PROGRESS", "COMPLETED", "DELAYED", "STALLED"]
    risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    return {
        "states": states,
        "project_types": project_types,
        "statuses": statuses,
        "risk_levels": risk_levels
    }


@router.get("/{project_id}", response_model=ProjectDetailOut)

def get_project_detail(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(func.upper(Project.project_id) == project_id.upper()).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found."
        )

    r = p.risk_score
    reasons = json.loads(r.reasons_json) if r and r.reasons_json else []

    # Duplicates linked to this project
    dups = db.query(DuplicateCandidate).filter(
        (DuplicateCandidate.project_a_id == p.project_id) | (DuplicateCandidate.project_b_id == p.project_id)
    ).all()

    dup_cards = []
    for d in dups:
        other_id = d.project_b_id if d.project_a_id == p.project_id else d.project_a_id
        other_p = db.query(Project).filter(Project.project_id == other_id).first()
        dup_cards.append({
            "id": d.id,
            "project_a_id": d.project_a_id,
            "project_b_id": d.project_b_id,
            "semantic_similarity": d.semantic_similarity,
            "distance_km": d.distance_km,
            "duplicate_score": d.duplicate_score,
            "status": d.status,
            "notes": d.notes,
            "created_at": d.created_at,
            "other_project_title": other_p.description if other_p else other_id,
            "other_project_state": other_p.state if other_p else "",
            "other_project_district": other_p.district if other_p else ""
        })

    # Recommended Actions
    actions = []
    if r and r.risk_level in ["HIGH", "CRITICAL"]:
        actions.append("Initiate priority site inspection by District Vigilance Officer.")
        if r.cost_risk >= 60:
            actions.append("Request itemized contractor measurement book (MB) and revised sanction justification.")
        if r.progress_gap_risk >= 60:
            actions.append("Halt further installment release until physical stage completion certificate is verified.")
        if dup_cards:
            actions.append("Conduct spatial asset audit to confirm no duplicate sanctioning of identical physical structure.")
    else:
        actions.append("Routine periodic progress reporting. No escalation required.")

    # AI Explanation paragraph
    ai_exp = (
        f"Project {p.project_id} has been evaluated with a risk rating of {r.risk_level if r else 'LOW'} "
        f"({r.overall_score if r else 0.0}/100). "
    )
    if reasons:
        ai_exp += "Key risk drivers include: " + "; ".join(reasons) + "."
    else:
        ai_exp += "Project metrics reflect nominal variance within expected tolerances."

    now = datetime.now(timezone.utc)
    cost_esc = max(0.0, ((p.expenditure - p.sanctioned_amount) / max(1.0, p.sanctioned_amount)) * 100.0)
    delay = 0
    if p.expected_completion_date and p.status != "COMPLETED" and p.physical_progress < 100.0:
        exp_d = p.expected_completion_date.replace(tzinfo=timezone.utc) if p.expected_completion_date.tzinfo is None else p.expected_completion_date
        if now > exp_d:
            delay = (now - exp_d).days

    detail = ProjectDetailOut.model_validate(p)
    detail.cost_escalation_pct = round(cost_esc, 1)
    detail.delay_days = delay
    detail.progress_gap_pct = round(p.financial_progress - p.physical_progress, 1)
    detail.alerts_count = len(p.alerts)
    detail.duplicates = dup_cards
    detail.ai_explanation = ai_exp
    detail.recommended_actions = actions

    return detail


@router.get("/{project_id}/nearby")
def find_nearby_projects(
    project_id: str,
    radius_km: float = Query(5.0, le=50.0),
    db: Session = Depends(get_db)
):
    target = db.query(Project).filter(func.upper(Project.project_id) == project_id.upper()).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target project not found.")

    import math
    delta_lat = (radius_km / 111.0) * 1.2
    lat_rad = math.radians(target.latitude)
    delta_lon = (radius_km / (111.0 * max(0.1, math.cos(lat_rad)))) * 1.2

    candidates = db.query(Project).filter(
        Project.project_id != target.project_id,
        Project.latitude.between(target.latitude - delta_lat, target.latitude + delta_lat),
        Project.longitude.between(target.longitude - delta_lon, target.longitude + delta_lon)
    ).all()

    nearby = []
    for p in candidates:
        dist = haversine_distance_km(target.latitude, target.longitude, p.latitude, p.longitude)
        if dist <= radius_km:
            r = p.risk_score
            reasons = json.loads(r.reasons_json) if r and r.reasons_json else []
            nearby.append({
                "project_id": p.project_id,
                "description": p.description,
                "project_type": p.project_type,
                "distance_km": round(dist, 3),
                "distance_meters": int(round(dist * 1000)),
                "latitude": p.latitude,
                "longitude": p.longitude,
                "sanctioned_amount": p.sanctioned_amount,
                "expenditure": p.expenditure,
                "physical_progress": p.physical_progress,
                "financial_progress": p.financial_progress,
                "status": p.status,
                "mp_id": p.mp_id,
                "implementing_agency": p.implementing_agency,
                "district": p.district,
                "state": p.state,
                "constituency": p.constituency,
                "risk_level": r.risk_level if r else "LOW",
                "overall_score": r.overall_score if r else 0.0,
                "reasons": reasons
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby


@router.get("/{project_id}/transactions", response_model=List[FinancialRecordOut])
def get_project_transactions(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch complete audit trail of financial disbursements and recipient payees for a specific project.
    """
    records = db.query(FinancialRecord).filter(
        func.upper(FinancialRecord.project_id) == project_id.upper()
    ).order_by(FinancialRecord.date.asc()).all()
    return records


@router.put("/{project_id}", response_model=ProjectDetailOut)
def admin_update_project(
    project_id: str,
    payload: ProjectAdminUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    National Nodal Administrator exclusive authority to update project master records,
    revise sanctioned capital, adjust physical progress, and modify official status.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only National Nodal Administrators can modify project master records."
        )

    project = db.query(Project).filter(func.upper(Project.project_id) == project_id.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.status:
        project.status = payload.status.upper()
    if payload.sanctioned_amount is not None:
        project.sanctioned_amount = payload.sanctioned_amount
    if payload.expenditure is not None:
        project.expenditure = payload.expenditure
    if payload.released_amount is not None:
        project.released_amount = payload.released_amount
    if payload.physical_progress is not None:
        project.physical_progress = payload.physical_progress

    # Recalculate financial progress %
    if project.sanctioned_amount > 0:
        project.financial_progress = round((project.expenditure / project.sanctioned_amount) * 100.0, 1)

    project.updated_at = datetime.now(timezone.utc)

    # Record administrative action in progress ledger
    admin_log = ProgressRecord(
        project_id=project.project_id,
        inspection_date=datetime.now(timezone.utc),
        physical_percentage=project.physical_progress,
        financial_percentage=project.financial_progress,
        remarks=f"ADMIN REVISION by {current_user.full_name} ({payload.order_reference or 'Order Ref N/A'}): {payload.administrative_remarks or 'Project master record updated.'}",
        inspector_name=current_user.full_name or "Nodal Administrator",
        photos_count=0
    )
    db.add(admin_log)
    db.commit()
    db.refresh(project)

    # Return refreshed detail view
    return get_project_detail(project.project_id, db)


@router.post("/{project_id}/investigation-report")
def submit_investigation_report(
    project_id: str,
    payload: InvestigationReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Central Vigilance Investigator authority to upload and record official field investigation reports,
    verified on-site physical stage %, and irregularity findings.
    """
    if current_user.role not in ["INVESTIGATOR", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Central Vigilance Investigators and Admins can file field reports."
        )

    project = db.query(Project).filter(func.upper(Project.project_id) == project_id.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    irregularities_text = ", ".join(payload.irregularities_observed) if payload.irregularities_observed else "None reported"
    formatted_remarks = (
        f"[FIELD INVESTIGATION REPORT - {payload.site_status}] "
        f"Verified Physical Stage: {payload.physical_verified_pct}% (Claimed: {project.physical_progress}%). "
        f"Findings: {payload.findings_summary}. "
        f"Irregularities: {irregularities_text}. "
        f"Recommendation: {payload.recommendation}."
    )
    if payload.document_ref:
        formatted_remarks += f" [Attached Document: {payload.document_ref}]"

    report_record = ProgressRecord(
        project_id=project.project_id,
        inspection_date=datetime.now(timezone.utc),
        physical_percentage=payload.physical_verified_pct,
        financial_percentage=project.financial_progress,
        remarks=formatted_remarks,
        inspector_name=payload.inspector_name or current_user.full_name,
        photos_count=1 if payload.document_ref else 0
    )
    db.add(report_record)

    # If severe irregularity flagged, generate or update alert
    if payload.site_status in ["IRREGULARITY_FOUND", "WORK_HALTED", "DUPLICATE_ASSET_CONFIRMED"]:
        alert = Alert(
            project_id=project.project_id,
            alert_type="FIELD_INVESTIGATION_IRREGULARITY",
            severity="CRITICAL",
            title=f"Field Audit Flag: {payload.site_status.replace('_', ' ')}",
            description=payload.findings_summary,
            status="INVESTIGATION_RECOMMENDED",
            assigned_to=current_user.full_name,
            resolution_notes=f"Recommendation: {payload.recommendation}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(alert)

    db.commit()

    return {
        "success": True,
        "message": f"Field Investigation Report recorded for project {project.project_id}",
        "report_id": report_record.id,
        "verified_percentage": payload.physical_verified_pct,
        "site_status": payload.site_status
    }


@router.post("/{project_id}/analyst-verification")
def submit_analyst_verification(
    project_id: str,
    payload: AnalystVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chief Data Analyst / ML Engineer authority to perform quantitative risk validation,
    document anomaly metrics, and formally escalate case to Nodal Admin.
    """
    if current_user.role not in ["ANALYST", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only Data Analysts and Administrators can submit ML verifications."
        )

    project = db.query(Project).filter(func.upper(Project.project_id) == project_id.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    indicators_text = ", ".join(payload.anomaly_indicators) if payload.anomaly_indicators else "Multivariate Anomaly Detected"
    formatted_remarks = (
        f"[ML ANALYST VALIDATION & ESCALATION - Confidence: {payload.confidence_score * 100:.1f}%] "
        f"Assessment: {payload.statistical_risk_assessment}. "
        f"Key Indicators: {indicators_text}. "
        f"Escalation Rationale: {payload.escalation_reason}. "
        f"Recommended Nodal Action: {payload.recommended_admin_action}."
    )

    review_record = ProgressRecord(
        project_id=project.project_id,
        inspection_date=datetime.now(timezone.utc),
        physical_percentage=project.physical_progress,
        financial_percentage=project.financial_progress,
        remarks=formatted_remarks,
        inspector_name=f"{payload.analyst_name} (ML Analyst)",
        photos_count=0
    )
    db.add(review_record)

    # Escalate existing open alerts for this project
    alerts = db.query(Alert).filter(Alert.project_id == project.project_id).all()
    for a in alerts:
        if a.status in ["OPEN", "PENDING"]:
            a.status = "UNDER_REVIEW"
            a.resolution_notes = f"Escalated by Data Analyst: {payload.recommended_admin_action}"
            a.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "success": True,
        "message": f"ML Analysis verification submitted and escalated to Nodal Administration for {project.project_id}",
        "confidence_score": payload.confidence_score,
        "action": payload.recommended_admin_action
    }

