import os
import shutil
import datetime
import logging
from typing import List, Optional, Dict, Any
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from dotenv import load_dotenv

# =========================
# Load Environment Variables
# =========================

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv()

# =========================
# AI Service
# =========================

from .ai_service import AIService

logger = logging.getLogger(__name__)
AIService.configure()

# =========================
# FastAPI Imports
# =========================

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# =========================
# Database Imports
# =========================

from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from .database import engine, get_db, Base
from . import models, auth

# =========================
# Internal Services
# =========================

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

# =========================
# Initialize Database
# =========================

Base.metadata.create_all(bind=engine)

# =========================
# FastAPI App
# =========================

app = FastAPI(
    title="SaaSMiner AI",
    version="1.0.0"
)

# =========================
# Health Check Route
# =========================


# =========================
# CORS Middleware
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Pydantic Schemas
# =========================

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

# =========================
# Auth Routes
# =========================

@app.post("/api/auth/register", response_model=UserResponse)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(
        models.User.email == user_data.email
    ).first()

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

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
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == username
    ).first()

    if not user or not auth.verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_me(
    current_user: models.User = Depends(auth.get_current_user)
):
    return current_user

# =========================
# Upload Project
# =========================

@app.post("/api/projects/upload")
def upload_project(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):

    proj_id = f"zip_{int(datetime.datetime.utcnow().timestamp())}"

    temp_zip = f"./uploads/{proj_id}.zip"
    extract_dir = f"./uploads/{proj_id}_src"

    try:

        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        source_dir = UploadService.extract_zip(
            temp_zip,
            extract_dir
        )

        scan_results = RepositoryScanner.scan_directory(
            source_dir
        )

        analysis_data = run_analysis_pipeline(
            scan_results,
            source_dir
        )

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

        report_path = f"./reports/report_{new_project.id}.pdf"

        analysis_detail = _build_report_detail(
            new_project,
            new_analysis,
            scan_results
        )

        ReportGenerator.generate_pdf(
            new_project.name,
            analysis_detail,
            report_path
        )

        new_report = models.Report(
            project_id=new_project.id,
            pdf_path=report_path
        )

        db.add(new_report)
        db.commit()

        UploadService.cleanup_directory(temp_zip)
        UploadService.cleanup_directory(extract_dir)

        return {
            "project_id": new_project.id,
            "message": "Scan completed successfully"
        }

    except Exception as e:

        UploadService.cleanup_directory(temp_zip)
        UploadService.cleanup_directory(extract_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Pipeline scan failed: {str(e)}"
        )

# =========================
# Analyze GitHub Repo
# =========================

@app.post("/api/projects/analyze-url")
def analyze_git_url(
    req: AnalyzeUrlRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):

    proj_id = f"git_{int(datetime.datetime.utcnow().timestamp())}"

    extract_dir = f"./uploads/{proj_id}_src"

    try:

        source_dir = UploadService.clone_github_repo(
            req.repo_url,
            extract_dir
        )

        scan_results = RepositoryScanner.scan_directory(
            source_dir
        )

        analysis_data = run_analysis_pipeline(
            scan_results,
            source_dir
        )

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

        UploadService.cleanup_directory(extract_dir)

        return {
            "project_id": new_project.id,
            "message": "Scan completed successfully"
        }

    except Exception as e:

        UploadService.cleanup_directory(extract_dir)

        raise HTTPException(
            status_code=500,
            detail=f"Git scan failed: {str(e)}"
        )

# =========================
# Analysis Pipeline
# =========================

def run_analysis_pipeline(
    scan_results: Dict[str, Any],
    source_dir: str
) -> dict:

    repo_summary = RepositorySummaryService.build_summary(
        scan_results,
        source_dir
    )

    modules = ModuleDetector.detect_modules(
        scan_results,
        repo_summary
    )

    domain_info = DomainDetector.detect_domain(
        scan_results,
        repo_summary
    )

    score_info = ProductScoreEngine.calculate_score(
        scan_results,
        modules,
        domain_info,
        repo_summary
    )

    saas_rec = SaaSRecommender.recommend(
        scan_results,
        modules,
        domain_info,
        score_info,
        repo_summary
    )

    apis = APIExtractor.extract_apis(
        scan_results,
        domain_info["domain"]
    )

    microservices = MicroserviceEngine.propose_microservices(
        modules,
        domain_info["domain"],
        repo_summary,
        apis
    )

    architecture = ArchitectureGenerator.generate_diagram(
        microservices,
        domain_info["domain"]
    )

    business = BusinessOpportunityEngine.analyze(
        domain_info["domain"],
        score_info["overall_score"],
        repo_summary,
        saas_rec
    )

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
# =========================
# Frontend (React/Vite) Serving
# =========================

FRONTEND_DIST = (
    Path(__file__).resolve().parent.parent / "frontend" / "dist"
)

if FRONTEND_DIST.exists():

    assets_dir = FRONTEND_DIST / "assets"

    if assets_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="assets",
        )

    @app.get("/")
    async def serve_frontend():
        return FileResponse(
            str(FRONTEND_DIST / "index.html")
        )

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):

        # FastAPI API routes
        if full_path.startswith("api"):
            raise HTTPException(status_code=404)

        requested_file = FRONTEND_DIST / full_path

        if requested_file.exists() and requested_file.is_file():
            return FileResponse(str(requested_file))

        # React Router fallback
        return FileResponse(
            str(FRONTEND_DIST / "index.html")
        )
# =========================
# Run Server
# =========================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port
    )