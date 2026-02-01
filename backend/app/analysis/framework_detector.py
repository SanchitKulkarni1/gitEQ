# app/analysis/framework_detector.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.analysis.symbols import SymbolRecord


@dataclass
class FrameworkDetection:
    """Result of framework detection"""
    name: str
    version: Optional[str] = None
    confidence: float = 0.0
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class FrameworkDetector:
    """Detects web frameworks and libraries from imports and file patterns"""
    
    # Framework patterns: {framework: {imports: [...], files: [...], content: [...]}}
    FRAMEWORKS = {
        # Python Backends
        "Django": {
            "imports": ["django", "django.conf", "django.urls", "django.http", "django.db"],
            "files": ["manage.py", "settings.py", "wsgi.py", "asgi.py"],
            "content": ["INSTALLED_APPS", "MIDDLEWARE", "django.contrib"],
        },
        "FastAPI": {
            "imports": ["fastapi", "fastapi.responses", "pydantic"],
            "files": [],
            "content": ["FastAPI()", "@app.get", "@app.post"],
        },
        "Flask": {
            "imports": ["flask", "flask.request", "flask.jsonify"],
            "files": ["app.py", "wsgi.py"],
            "content": ["Flask(__name__)", "@app.route"],
        },
        
        # JavaScript/TypeScript Backends
        "Express.js": {
            "imports": ["express", "express-validator"],
            "files": ["server.js", "app.js"],
            "content": ["express()", "app.listen", "app.get", "app.post", "express.Router"],
        },
        "NestJS": {
            "imports": ["@nestjs/core", "@nestjs/common", "@nestjs/platform-express"],
            "files": ["main.ts", "app.module.ts"],
            "content": ["@Controller", "@Get", "@Post", "@Module", "NestFactory"],
        },
        "Koa": {
            "imports": ["koa", "koa-router"],
            "files": ["server.js", "app.js"],
            "content": ["new Koa()", "ctx.body"],
        },
        "Hapi": {
            "imports": ["@hapi/hapi"],
            "files": [],
            "content": ["Hapi.server", "server.route"],
        },
        
        # Frontend Frameworks
        "React": {
            "imports": ["react", "react-dom", "react/jsx-runtime"],
            "files": ["App.tsx", "App.jsx", "index.tsx"],
            "content": ["React.Component", "useState", "useEffect", "createRoot"],
        },
        "Next.js": {
            "imports": ["next", "next/router", "next/link", "next/image"],
            "files": ["next.config.js", "pages/_app", "app/layout"],
            "content": ["getServerSideProps", "getStaticProps", "NextPage"],
        },
        "Vue": {
            "imports": ["vue", "@vue/runtime-core"],
            "files": ["App.vue", "main.js"],
            "content": ["createApp", "Vue.component", "<template>"],
        },
        "Nuxt": {
            "imports": ["nuxt", "@nuxt/kit"],
            "files": ["nuxt.config.ts", "nuxt.config.js"],
            "content": ["defineNuxtConfig", "useNuxtApp"],
        },
        "Angular": {
            "imports": ["@angular/core", "@angular/common"],
            "files": ["angular.json", "app.module.ts"],
            "content": ["@Component", "@NgModule", "@Injectable"],
        },
        "Svelte": {
            "imports": ["svelte"],
            "files": ["App.svelte"],
            "content": ["<script>", "<style>", "export let"],
        },
        "SvelteKit": {
            "imports": ["@sveltejs/kit"],
            "files": ["svelte.config.js"],
            "content": ["export const load"],
        },
        
        # Go Frameworks
        "Gin": {
            "imports": [],  # Go doesn't use JS-style imports
            "files": ["main.go"],
            "content": ["gin.Default()", "gin.Engine", 'c.JSON', 'router.GET'],
        },
        "Echo": {
            "imports": [],
            "files": ["main.go"],
            "content": ["echo.New()", "c.String", "e.GET"],
        },
        "Fiber": {
            "imports": [],
            "files": ["main.go"],
            "content": ["fiber.New()", "c.SendString", "app.Get"],
        },
        
        # Mobile
        "React Native": {
            "imports": ["react-native", "react-native/Libraries"],
            "files": ["App.tsx", "app.json", "metro.config.js"],
            "content": ["AppRegistry", "StyleSheet.create"],
        },
        "Flutter": {
            "imports": [],
            "files": ["pubspec.yaml", "lib/main.dart"],
            "content": ["flutter:", "StatelessWidget", "StatefulWidget"],
        },
        
        # Desktop
        "Electron": {
            "imports": ["electron"],
            "files": ["main.js", "preload.js"],
            "content": ["BrowserWindow", "app.whenReady"],
        },
        "Tauri": {
            "imports": ["@tauri-apps/api"],
            "files": ["tauri.conf.json", "src-tauri/"],
            "content": ["tauri::Builder", "#[tauri::command]"],
        },
    }
    
    def __init__(self, files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]):
        self.files = files
        self.symbols = symbols
        self.file_contents = file_contents
        self.import_names = [s.name.lower() for s in symbols if s.kind == "import"]
        self.all_content = " ".join(file_contents.values()).lower()
    
    def detect_all(self) -> List[FrameworkDetection]:
        """Detect all frameworks present in the codebase"""
        detected = []
        
        for framework_name, patterns in self.FRAMEWORKS.items():
            detection = self._detect_framework(framework_name, patterns)
            if detection.confidence > 0.3:  # Threshold
                detected.append(detection)
        
        # Sort by confidence
        detected.sort(key=lambda x: x.confidence, reverse=True)
        return detected
    
    def detect_primary(self) -> Optional[FrameworkDetection]:
        """Detect the primary framework (highest confidence)"""
        all_frameworks = self.detect_all()
        return all_frameworks[0] if all_frameworks else None
    
    def _detect_framework(self, name: str, patterns: Dict) -> FrameworkDetection:
        """Detect a specific framework based on patterns"""
        evidence = []
        confidence = 0.0
        
        # Check imports (40% weight)
        import_matches = 0
        for pattern in patterns.get("imports", []):
            if any(pattern.lower() in imp for imp in self.import_names):
                import_matches += 1
                evidence.append(f"Import: {pattern}")
        
        if patterns.get("imports"):
            import_confidence = (import_matches / len(patterns["imports"])) * 0.4
            confidence += import_confidence
        
        # Check files (30% weight)
        file_matches = 0
        for pattern in patterns.get("files", []):
            if any(pattern.lower() in f.lower() for f in self.files):
                file_matches += 1
                evidence.append(f"File: {pattern}")
        
        if patterns.get("files"):
            file_confidence = (file_matches / len(patterns["files"])) * 0.3
            confidence += file_confidence
        
        # Check content patterns (30% weight)
        content_matches = 0
        for pattern in patterns.get("content", []):
            if pattern.lower() in self.all_content:
                content_matches += 1
                evidence.append(f"Pattern: {pattern}")
        
        if patterns.get("content"):
            content_confidence = (content_matches / len(patterns["content"])) * 0.3
            confidence += content_confidence
        
        return FrameworkDetection(
            name=name,
            confidence=min(confidence, 1.0),  # Cap at 1.0
            evidence=evidence[:5],  # Keep top 5 evidence items
        )
    
    def categorize_framework(self, framework: FrameworkDetection) -> str:
        """Categorize framework type (frontend, backend, mobile, etc.)"""
        frontend = ["React", "Next.js", "Vue", "Nuxt", "Angular", "Svelte", "SvelteKit"]
        backend = ["Django", "FastAPI", "Flask", "Express.js", "NestJS", "Koa", "Hapi", "Gin", "Echo", "Fiber"]
        mobile = ["React Native", "Flutter"]
        desktop = ["Electron", "Tauri"]
        
        if framework.name in frontend:
            return "frontend"
        elif framework.name in backend:
            return "backend"
        elif framework.name in mobile:
            return "mobile"
        elif framework.name in desktop:
            return "desktop"
        
        return "unknown"


def detect_frameworks(files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]) -> Tuple[Optional[FrameworkDetection], List[FrameworkDetection]]:
    """
    Convenience function to detect frameworks.
    
    Returns:
        (primary_framework, all_detected_frameworks)
    """
    detector = FrameworkDetector(files, symbols, file_contents)
    all_frameworks = detector.detect_all()
    primary = all_frameworks[0] if all_frameworks else None
    
    return primary, all_frameworks