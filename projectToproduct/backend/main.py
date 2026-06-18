import os
import shutil
import datetime
import logging
from typing import List, Optional, Dict, Any

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()

from .ai_service import AIService

logger = logging.getLogger(__name__)
AIService.configure()
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from .database import engine, get_db, Base
from . import models, auth
from .upload_service import UploadService
from .repository_scanner import RepositoryScanner
from .module_detector import ModuleDetector
from .domain_detector import DomainDetector
from .product_score_engine import ProductScoreEngine
from .saas_recommender import SaaSRecommender
from .api_extractor import APIExtractor
from .microservice_engine import MicroserviceEngine
from .architecture_generator import ArchitectureGenerator
from .business_engine import BusinessOpportunityEngine
from .report_generator import ReportGenerator
from .repository_summary_service import RepositorySummaryService

# Initialize DB
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaSMiner AI", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    fullname: str

class UserResponse(BaseModel):
    id: int
    email: str
    fullname: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class AnalyzeUrlRequest(BaseModel):
    name: str
    repo_url: str

# Auth Routes
@app.post("/api/auth/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = auth.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        fullname=user_data.fullname
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", response_model=Token)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# Project Scan Pipeline Endpoint (Zip)
@app.post("/api/projects/upload")
def upload_project(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Setup temporary directory paths
    proj_id = f"zip_{int(datetime.datetime.utcnow().timestamp())}"
    temp_zip = f"./uploads/{proj_id}.zip"
    extract_dir = f"./uploads/{proj_id}_src"

    try:
        # Save uploaded zip
        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract Zip
        source_dir = UploadService.extract_zip(temp_zip, extract_dir)

        # Run Scan & Pipeline
        scan_results = RepositoryScanner.scan_directory(source_dir)
        analysis_data = run_analysis_pipeline(scan_results, source_dir)

        # Save to DB
        new_project = models.Project(
            user_id=current_user.id,
            name=name,
            repo_url=None,
            file_count=scan_results["file_count"],
            folder_count=scan_results["folder_count"],
            languages=scan_results["languages"]
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        new_analysis = models.AnalysisResult(
            project_id=new_project.id,
            domain=analysis_data["domain"],
            confidence=analysis_data["confidence"],
            modules=analysis_data["modules"],
            potential_score=analysis_data["potential_score"],
            saas_recommendation=analysis_data["saas_recommendation"],
            apis=analysis_data["apis"],
            microservices=analysis_data["microservices"],
            architecture=analysis_data["architecture"],
            business_potential=analysis_data["business_potential"]
        )
        db.add(new_analysis)
        db.commit()

        # Generate PDF Report
        report_path = f"./reports/report_{new_project.id}.pdf"
        analysis_detail = _build_report_detail(new_project, new_analysis, scan_results)
        ReportGenerator.generate_pdf(new_project.name, analysis_detail, report_path)

        new_report = models.Report(
            project_id=new_project.id,
            pdf_path=report_path
        )
        db.add(new_report)
        db.commit()

        # Clean source folders
        UploadService.cleanup_directory(temp_zip)
        UploadService.cleanup_directory(extract_dir)

        return {"project_id": new_project.id, "message": "Scan completed successfully"}

    except Exception as e:
        UploadService.cleanup_directory(temp_zip)
        UploadService.cleanup_directory(extract_dir)
        raise HTTPException(status_code=500, detail=f"Pipeline scan failed: {str(e)}")


# Project Scan Pipeline Endpoint (Github URL)
@app.post("/api/projects/analyze-url")
def analyze_git_url(
    req: AnalyzeUrlRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    proj_id = f"git_{int(datetime.datetime.utcnow().timestamp())}"
    extract_dir = f"./uploads/{proj_id}_src"

    try:
        source_dir = UploadService.clone_github_repo(req.repo_url, extract_dir)

        # Run Scan & Pipeline
        scan_results = RepositoryScanner.scan_directory(source_dir)
        analysis_data = run_analysis_pipeline(scan_results, source_dir)

        # Save to DB
        new_project = models.Project(
            user_id=current_user.id,
            name=req.name,
            repo_url=req.repo_url,
            file_count=scan_results["file_count"],
            folder_count=scan_results["folder_count"],
            languages=scan_results["languages"]
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        new_analysis = models.AnalysisResult(
            project_id=new_project.id,
            domain=analysis_data["domain"],
            confidence=analysis_data["confidence"],
            modules=analysis_data["modules"],
            potential_score=analysis_data["potential_score"],
            saas_recommendation=analysis_data["saas_recommendation"],
            apis=analysis_data["apis"],
            microservices=analysis_data["microservices"],
            architecture=analysis_data["architecture"],
            business_potential=analysis_data["business_potential"]
        )
        db.add(new_analysis)
        db.commit()

        # Generate PDF Report
        report_path = f"./reports/report_{new_project.id}.pdf"
        analysis_detail = _build_report_detail(new_project, new_analysis, scan_results)
        ReportGenerator.generate_pdf(new_project.name, analysis_detail, report_path)

        new_report = models.Report(
            project_id=new_project.id,
            pdf_path=report_path
        )
        db.add(new_report)
        db.commit()

        # Cleanup source folders
        UploadService.cleanup_directory(extract_dir)

        return {"project_id": new_project.id, "message": "Scan completed successfully"}

    except Exception as e:
        UploadService.cleanup_directory(extract_dir)
        raise HTTPException(status_code=500, detail=f"Git scan failed: {str(e)}")


def run_analysis_pipeline(scan_results: Dict[str, Any], source_dir: str) -> dict:
    """Invokes all intelligence engines sequentially with Gemini-powered analysis."""
    repo_summary = RepositorySummaryService.build_summary(scan_results, source_dir)

    modules = ModuleDetector.detect_modules(scan_results, repo_summary)
    domain_info = DomainDetector.detect_domain(scan_results, repo_summary)

    score_info = ProductScoreEngine.calculate_score(
        scan_results, modules, domain_info, repo_summary
    )
    saas_rec = SaaSRecommender.recommend(
        scan_results, modules, domain_info, score_info, repo_summary
    )

    apis = APIExtractor.extract_apis(scan_results, domain_info["domain"])
    microservices = MicroserviceEngine.propose_microservices(
        modules, domain_info["domain"], repo_summary, apis
    )

    architecture = ArchitectureGenerator.generate_diagram(
        microservices, domain_info["domain"]
    )
    business = BusinessOpportunityEngine.analyze(
        domain_info["domain"],
        score_info["overall_score"],
        repo_summary,
        saas_rec,
    )

    # Embed AI metadata in existing JSON columns for backward-compatible persistence
    saas_rec = {
        **saas_rec,
        "score_breakdown": score_info.get("breakdown", {}),
        "category_scores": score_info.get("category_scores", {}),
        "score_reasoning": score_info.get("reasoning", ""),
        "domain_reasoning": domain_info.get("reasoning", domain_info.get("description", "")),
        "ai_powered": AIService.is_available(),
    }
    business = {
        **business,
        "domain_reasoning": domain_info.get("reasoning", domain_info.get("description", "")),
    }

    return {
        "domain": domain_info["domain"],
        "confidence": domain_info["confidence"],
        "modules": modules,
        "potential_score": score_info["overall_score"],
        "saas_recommendation": saas_rec,
        "apis": apis,
        "microservices": microservices,
        "architecture": architecture,
        "business_potential": business,
    }


def _build_report_detail(
    project,
    analysis,
    scan_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compile analysis payload for PDF generation."""
    saas_rec = analysis.saas_recommendation or {}
    business = analysis.business_potential or {}

    return {
        "potential_score": analysis.potential_score,
        "domain": analysis.domain,
        "confidence": analysis.confidence,
        "domain_reasoning": saas_rec.get("domain_reasoning") or business.get("domain_reasoning", ""),
        "score_breakdown": saas_rec.get("score_breakdown", {}),
        "category_scores": saas_rec.get("category_scores", {}),
        "score_reasoning": saas_rec.get("score_reasoning", ""),
        "saas_recommendation": saas_rec,
        "business_potential": business,
        "file_count": project.file_count,
        "folder_count": project.folder_count,
        "languages": project.languages,
        "tech_stack": (scan_results or {}).get("tech_stack", list((project.languages or {}).keys())),
        "modules": analysis.modules or [],
        "apis": analysis.apis or [],
        "microservices": analysis.microservices or {},
        "architecture": analysis.architecture or {},
        "created_at": project.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


# Dashboard & Project Management Routes
@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    projects = db.query(models.Project).filter(models.Project.user_id == current_user.id).order_by(models.Project.created_at.desc()).all()
    results = []
    for p in projects:
        ar = db.query(models.AnalysisResult).filter(models.AnalysisResult.project_id == p.id).first()
        results.append({
            "id": p.id,
            "name": p.name,
            "repo_url": p.repo_url,
            "file_count": p.file_count,
            "folder_count": p.folder_count,
            "languages": p.languages,
            "created_at": p.created_at,
            "domain": ar.domain if ar else "N/A",
            "potential_score": ar.potential_score if ar else 0
        })
    return results

@app.get("/api/projects/{project_id}")
def get_project_details(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    analysis = db.query(models.AnalysisResult).filter(models.AnalysisResult.project_id == project.id).first()
    report = db.query(models.Report).filter(models.Report.project_id == project.id).first()

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "repo_url": project.repo_url,
            "file_count": project.file_count,
            "folder_count": project.folder_count,
            "languages": project.languages,
            "created_at": project.created_at
        },
        "analysis": {
            "domain": analysis.domain if analysis else "N/A",
            "confidence": analysis.confidence if analysis else 0,
            "modules": analysis.modules if analysis else [],
            "potential_score": analysis.potential_score if analysis else 0,
            "saas_recommendation": analysis.saas_recommendation if analysis else {},
            "apis": analysis.apis if analysis else [],
            "microservices": analysis.microservices if analysis else {},
            "architecture": analysis.architecture if analysis else {},
            "business_potential": analysis.business_potential if analysis else {}
        },
        "report_ready": report is not None
    }

@app.delete("/api/projects/{project_id}")
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    report = db.query(models.Report).filter(models.Report.project_id == project_id).first()
    if report and os.path.exists(report.pdf_path):
        try:
            os.remove(report.pdf_path)
        except Exception:
            pass

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


@app.get("/api/projects/{project_id}/report")
def download_report(
    project_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    analysis = db.query(models.AnalysisResult).filter(models.AnalysisResult.project_id == project_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis data found for this project")

    # Always regenerate the PDF on-the-fly using the latest report generator code
    report_path = f"./reports/report_{project.id}.pdf"
    analysis_detail = _build_report_detail(project, analysis)

    try:
        ReportGenerator.generate_pdf(project.name, analysis_detail, report_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

    # Ensure Report record exists in DB
    report = db.query(models.Report).filter(models.Report.project_id == project_id).first()
    if not report:
        report = models.Report(project_id=project.id, pdf_path=report_path)
        db.add(report)
        db.commit()
        
    return FileResponse(
        report_path, 
        media_type="application/pdf", 
        filename=f"Report_{project.name.replace(' ', '_')}.pdf"
    )


@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    projects = db.query(models.Project).filter(models.Project.user_id == current_user.id).all()
    
    total_projects = len(projects)
    if total_projects == 0:
        return {
            "total_projects": 0,
            "avg_score": 0,
            "highest_score": 0,
            "language_counts": {},
            "scanned_apis": 0
        }
        
    project_ids = [p.id for p in projects]
    analyses = db.query(models.AnalysisResult).filter(models.AnalysisResult.project_id.in_(project_ids)).all()
    
    scores = [a.potential_score for a in analyses]
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    highest_score = max(scores) if scores else 0
    
    # Aggregated languages
    languages = {}
    for p in projects:
        if p.languages:
            for lang, count in p.languages.items():
                languages[lang] = languages.get(lang, 0) + count
                
    # Scanned APIs
    total_apis = sum(len(a.apis or []) for a in analyses)

    return {
        "total_projects": total_projects,
        "avg_score": avg_score,
        "highest_score": highest_score,
        "language_counts": languages,
        "scanned_apis": total_apis
    }
