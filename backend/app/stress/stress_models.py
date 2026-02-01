# app/stress/stress_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional
from enum import Enum


class ArchitectureType(str, Enum):
    """Detected architecture types"""
    STATIC_SPA = "static_spa"  # React, Vue, Angular without SSR
    SSR_APP = "ssr_app"  # Next.js, Nuxt, SvelteKit with server
    BACKEND_API = "backend_api"  # Express, FastAPI, Django
    FULL_STACK = "full_stack"  # Combined frontend + backend
    MONOREPO = "monorepo"  # Multi-package repository
    
    # 🚨 ADD THESE MISSING TYPES TO FIX THE ERROR:
    REST_API = "rest_api"
    GRAPHQL_API = "graphql_api"
    MICROSERVICES = "microservices"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"        # <--- This is the specific one crashing your code
    
    UNKNOWN = "unknown"


class TechStack(BaseModel):
    """Detected technology stack"""
    framework: Optional[str] = None  # React, Next.js, Vue, etc.
    language: Optional[str] = None  # TypeScript, JavaScript, Python
    backend: Optional[str] = None  # Express, FastAPI, None
    database: Optional[str] = None  # PostgreSQL, MongoDB, None
    deployment: Optional[str] = None  # Vercel, AWS, Docker
    has_ssr: bool = False
    has_api_routes: bool = False
    is_static: bool = True


class StressVector(BaseModel):
    """Defines a stress scenario"""
    name: str
    description: str
    target_layers: List[str]
    severity: float = Field(ge=0.0, le=1.0)
    propagation_type: Literal["traffic", "dependency", "data", "auth"] = "traffic"
    architecture_types: List[ArchitectureType] = Field(
        default_factory=lambda: [ArchitectureType.UNKNOWN]
    )
    min_severity_threshold: float = 0.5


class BottleneckAnalysis(BaseModel):
    """Specific bottleneck identified"""
    component: str
    reason: str
    severity: Literal["critical", "high", "medium", "low"]
    recommendation: str
    file_path: Optional[str] = None


class StressResult(BaseModel):
    """Result of stress test analysis"""
    stress: str
    architecture_type: ArchitectureType
    tech_stack: TechStack
    is_applicable: bool = True
    violated_assumptions: List[Dict]
    affected_files: List[str]
    impact_path: List[str]
    bottlenecks: List[BottleneckAnalysis] = Field(default_factory=list)
    failure_mode: str
    confidence: float = Field(ge=0.0, le=1.0)
    recommendations: List[str] = Field(default_factory=list)
    safe_components: List[str] = Field(default_factory=list)


class RepoContext(BaseModel):
    """Context about the repository"""
    architecture_type: ArchitectureType
    tech_stack: TechStack
    total_files: int
    has_tests: bool = False
    has_ci_cd: bool = False
    bundle_size_estimate: Optional[int] = None
    dependencies_count: int = 0