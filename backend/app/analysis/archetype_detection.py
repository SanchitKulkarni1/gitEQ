"""
Unified Architecture Detector
Replaces the old archetype_detection.py with comprehensive architecture detection
Integrates with stress testing module's ArchitectureType enum
"""

from typing import Dict, List, Optional
from app.analysis.symbols import SymbolRecord
from app.analysis.framework_detector import detect_frameworks, FrameworkDetector
from app.analysis.database_detector import detect_database

# Import from stress module for consistency
try:
    from app.stress.stress_models import ArchitectureType, TechStack, RepoContext
except ImportError:
    # Fallback if stress module not available
    from enum import Enum
    
    class ArchitectureType(str, Enum):
        STATIC_SPA = "static_spa"
        SSR_APP = "ssr_app"
        REST_API = "rest_api"
        GRAPHQL_API = "graphql_api"
        MICROSERVICES = "microservices"
        FULL_STACK = "full_stack"
        BACKEND_API = "backend_api"
        CLI_TOOL = "cli_tool"
        LIBRARY = "library"
        UNKNOWN = "unknown"


class UnifiedArchitectureDetector:
    """
    Comprehensive architecture detector that handles all project types:
    - Frontend (React, Vue, Angular, etc.)
    - Backend (Django, FastAPI, Express, Go, etc.)
    - Full-stack (Next.js, Nuxt, etc.)
    - Mobile (React Native, Flutter)
    - Desktop (Electron, Tauri)
    - CLI tools, Libraries, Data pipelines
    """
    
    def __init__(self, files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]):
        self.files = files
        self.symbols = symbols
        self.file_contents = file_contents
        
        # Pre-compute common properties
        self.file_extensions = self._get_file_extensions()
        self.import_names = [s.name.lower() for s in symbols if s.kind == "import"]
        self.all_content = " ".join(file_contents.values()).lower()
        
        # Detect frameworks and database
        self.primary_framework, self.all_frameworks = detect_frameworks(files, symbols, file_contents)
        self.database = detect_database(files, symbols, file_contents)
    
    def detect(self) -> Dict:
        """
        Main detection method. Returns complete architecture information.
        
        Returns:
            {
                "archetype": str (for backward compatibility),
                "architecture_type": ArchitectureType,
                "tech_stack": TechStack,
                "confidence": float,
                "evidence": List[str]
            }
        """
        # Detect architecture type
        architecture_type, confidence, evidence = self._detect_architecture_type()
        
        # Build tech stack
        tech_stack = self._build_tech_stack()
        
        # Map to old "archetype" for backward compatibility
        archetype = self._map_to_archetype(architecture_type)
        
        return {
            "archetype": archetype,  # Backward compatibility
            "architecture_type": architecture_type,
            "tech_stack": tech_stack,
            "confidence": confidence,
            "evidence": evidence,
        }
    
    def _detect_architecture_type(self) -> tuple[ArchitectureType, float, List[str]]:
        """Detect specific architecture type with confidence score"""
        
        # Check for microservices
        if self._is_microservices():
            return ArchitectureType.MICROSERVICES, 0.85, ["Multiple service directories detected"]
        
        # Check for mobile apps
        if self._is_mobile_app():
            return ArchitectureType.STATIC_SPA, 0.9, ["Mobile framework detected"]
        
        # Check for desktop apps
        if self._is_desktop_app():
            return ArchitectureType.STATIC_SPA, 0.9, ["Desktop framework detected"]
        
        # Check for CLI tools
        if self._is_cli_tool():
            return ArchitectureType.CLI_TOOL, 0.8, ["CLI patterns detected"]
        
        # Check for library/SDK
        if self._is_library():
            return ArchitectureType.LIBRARY, 0.75, ["Library structure detected"]
        
        # Check for GraphQL API
        if self._is_graphql():
            return ArchitectureType.GRAPHQL_API, 0.85, ["GraphQL schema/resolvers detected"]
        
        # Check for full-stack (Next.js, Nuxt, etc.)
        if self._is_full_stack():
            return ArchitectureType.FULL_STACK, 0.9, ["Full-stack framework detected"]
        
        # Check for SSR app
        if self._is_ssr_app():
            return ArchitectureType.SSR_APP, 0.85, ["SSR framework detected"]
        
        # Check for backend API
        if self._is_backend_api():
            return ArchitectureType.BACKEND_API, 0.85, ["Backend framework detected"]
        
        # Check for static SPA
        if self._is_static_spa():
            return ArchitectureType.STATIC_SPA, 0.8, ["Frontend framework detected"]
        
        # Unknown
        return ArchitectureType.UNKNOWN, 0.3, ["Could not determine architecture type"]
    
    def _is_microservices(self) -> bool:
        """Detect microservices architecture"""
        # Check for multiple service directories
        service_dirs = [
            "services/", "/services/",
            "apps/", "/apps/",
            "packages/", "/packages/",
        ]
        
        service_count = sum(
            1 for pattern in service_dirs
            if sum(1 for f in self.files if pattern in f) > 3
        )
        
        # Proto files indicate gRPC microservices
        has_proto = any(f.endswith(".proto") for f in self.files)
        
        # Docker compose with multiple services
        has_compose = any("docker-compose" in f for f in self.files)
        multiple_dockerfiles = sum(1 for f in self.files if "dockerfile" in f.lower()) > 1
        
        return service_count >= 2 or (has_proto and has_compose) or multiple_dockerfiles
    
    def _is_mobile_app(self) -> bool:
        """Detect mobile app (React Native, Flutter)"""
        if self.primary_framework and self.primary_framework.name in ["React Native", "Flutter"]:
            return True
        
        mobile_files = ["app.json", "metro.config.js", "pubspec.yaml"]
        return any(f in self.files for f in mobile_files)
    
    def _is_desktop_app(self) -> bool:
        """Detect desktop app (Electron, Tauri)"""
        if self.primary_framework and self.primary_framework.name in ["Electron", "Tauri"]:
            return True
        
        desktop_files = ["electron-builder.json", "tauri.conf.json"]
        return any(f in self.files for f in desktop_files)
    
    def _is_cli_tool(self) -> bool:
        """Detect CLI tool"""
        cli_indicators = [
            "cli.py", "main.py", "cmd/", "__main__.py",
            "bin/", "scripts/",
        ]
        
        has_cli_structure = any(
            indicator in f.lower() for f in self.files
            for indicator in cli_indicators
        )
        
        # CLI libraries
        cli_libs = ["click", "argparse", "typer", "commander", "yargs"]
        has_cli_lib = any(lib in self.import_names for lib in cli_libs)
        
        # No web framework
        has_web_framework = self.primary_framework is not None and \
                           self.primary_framework.name not in ["React", "Vue", "Angular"]
        
        return (has_cli_structure or has_cli_lib) and not has_web_framework
    
    def _is_library(self) -> bool:
        """Detect library/SDK"""
        library_indicators = [
            "setup.py", "pyproject.toml", "package.json",
            "__init__.py", "index.ts", "lib/", "src/lib/",
        ]
        
        has_lib_structure = sum(
            1 for indicator in library_indicators
            if any(indicator in f.lower() for f in self.files)
        ) >= 2
        
        # No main entry point for apps
        no_app_entry = not any(
            f in self.files for f in ["main.py", "app.py", "server.js", "index.html"]
        )
        
        # Has exports
        has_exports = "export" in self.all_content or "__all__" in self.all_content
        
        return has_lib_structure and (no_app_entry or has_exports)
    
    def _is_graphql(self) -> bool:
        """Detect GraphQL API"""
        graphql_files = [
            ".graphql", ".gql", "schema.graphql", "resolvers/",
        ]
        
        has_graphql_files = any(
            pattern in f.lower() for f in self.files
            for pattern in graphql_files
        )
        
        graphql_libs = ["graphql", "apollo-server", "@apollo/server", "type-graphql"]
        has_graphql_lib = any(lib in self.import_names for lib in graphql_libs)
        
        return has_graphql_files or has_graphql_lib
    
    def _is_full_stack(self) -> bool:
        """Detect full-stack framework (Next.js, Nuxt, etc.)"""
        if not self.primary_framework:
            return False
        
        fullstack_frameworks = ["Next.js", "Nuxt", "SvelteKit"]
        if self.primary_framework.name in fullstack_frameworks:
            return True
        
        # Check for API routes in frontend frameworks
        has_api_routes = any(
            "pages/api/" in f or "app/api/" in f or "routes/api/" in f
            for f in self.files
        )
        
        has_frontend = self.primary_framework.name in ["React", "Vue", "Svelte"]
        
        return has_frontend and has_api_routes
    
    def _is_ssr_app(self) -> bool:
        """Detect SSR app (without full API routes)"""
        if not self.primary_framework:
            return False
        
        # Already detected as full-stack
        if self._is_full_stack():
            return False
        
        # Check for SSR patterns
        ssr_patterns = [
            "getServerSideProps", "getStaticProps", "getInitialProps",
            "server.ts", "server.js",
        ]
        
        has_ssr = any(pattern in self.all_content for pattern in ssr_patterns)
        
        return has_ssr
    
    def _is_backend_api(self) -> bool:
        """Detect pure backend API"""
        if not self.primary_framework:
            # Check for backend patterns without framework
            backend_patterns = [
                "/routes/", "/controllers/", "/handlers/",
                "/api/", "/endpoints/", "/services/",
            ]
            has_backend_structure = sum(
                1 for pattern in backend_patterns
                if any(pattern in f for f in self.files)
            ) >= 2
            
            if has_backend_structure:
                return True
            
            return False
        
        backend_frameworks = [
            "Django", "FastAPI", "Flask",
            "Express.js", "NestJS", "Koa", "Hapi",
            "Gin", "Echo", "Fiber",
        ]
        
        is_backend_framework = self.primary_framework.name in backend_frameworks
        
        # Make sure it's not also a frontend
        has_frontend_files = any(
            f.endswith((".tsx", ".jsx", ".vue", ".svelte"))
            for f in self.files
        )
        
        return is_backend_framework and not has_frontend_files
    
    def _is_static_spa(self) -> bool:
        """Detect static SPA"""
        if not self.primary_framework:
            return False
        
        frontend_frameworks = ["React", "Vue", "Angular", "Svelte"]
        
        return self.primary_framework.name in frontend_frameworks
    
    def _build_tech_stack(self) -> Dict:
        """Build tech stack dictionary"""
        return {
            "framework": self.primary_framework.name if self.primary_framework else None,
            "language": self._detect_primary_language(),
            "backend": self._detect_backend_framework(),
            "database": self.database.database_type if self.database else None,
            "orm": self.database.orm if self.database else None,
            "has_ssr": self._is_ssr_app() or self._is_full_stack(),
            "has_api_routes": self._has_api_routes(),
            "is_static": self._is_static_spa(),
        }
    
    def _detect_primary_language(self) -> str:
        """Detect primary programming language"""
        language_counts = {
            "TypeScript": sum(1 for ext in self.file_extensions if ext in [".ts", ".tsx"]),
            "JavaScript": sum(1 for ext in self.file_extensions if ext in [".js", ".jsx"]),
            "Python": sum(1 for ext in self.file_extensions if ext == ".py"),
            "Go": sum(1 for ext in self.file_extensions if ext == ".go"),
            "Rust": sum(1 for ext in self.file_extensions if ext == ".rs"),
            "Java": sum(1 for ext in self.file_extensions if ext == ".java"),
            "Ruby": sum(1 for ext in self.file_extensions if ext == ".rb"),
        }
        
        return max(language_counts, key=language_counts.get) if max(language_counts.values()) > 0 else "Unknown"
    
    def _detect_backend_framework(self) -> Optional[str]:
        """Detect backend framework specifically"""
        backend_frameworks = [
            "Django", "FastAPI", "Flask",
            "Express.js", "NestJS", "Koa", "Hapi",
            "Gin", "Echo", "Fiber",
        ]
        
        for framework in self.all_frameworks:
            if framework.name in backend_frameworks:
                return framework.name
        
        return None
    
    def _has_api_routes(self) -> bool:
        """Check if project has API routes"""
        api_patterns = [
            "/api/", "/routes/", "/controllers/",
            "/endpoints/", "/handlers/",
            "pages/api/", "app/api/",
        ]
        
        return any(
            pattern in f.lower() for f in self.files
            for pattern in api_patterns
        )
    
    def _get_file_extensions(self) -> List[str]:
        """Get all unique file extensions"""
        extensions = set()
        for f in self.files:
            if "." in f:
                ext = "." + f.split(".")[-1]
                extensions.add(ext)
        return list(extensions)
    
    def _map_to_archetype(self, architecture_type: ArchitectureType) -> str:
        """Map ArchitectureType to old archetype string for backward compatibility"""
        mapping = {
            ArchitectureType.STATIC_SPA: "frontend",
            ArchitectureType.SSR_APP: "frontend",
            ArchitectureType.BACKEND_API: "backend",
            ArchitectureType.REST_API: "backend",
            ArchitectureType.GRAPHQL_API: "backend",
            ArchitectureType.FULL_STACK: "fullstack",
            ArchitectureType.MICROSERVICES: "backend",
            ArchitectureType.CLI_TOOL: "unknown",
            ArchitectureType.LIBRARY: "unknown",
            ArchitectureType.UNKNOWN: "unknown",
        }
        
        return mapping.get(architecture_type, "unknown")


def detect_architecture(files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]) -> Dict:
    """
    Convenience function to detect architecture.
    
    Returns:
        Complete architecture information including archetype, architecture_type, tech_stack
    """
    detector = UnifiedArchitectureDetector(files, symbols, file_contents)
    return detector.detect()

# ==========================================
# 🚨 BACKWARD COMPATIBILITY FIX
# ==========================================
detect_archetype = detect_architecture