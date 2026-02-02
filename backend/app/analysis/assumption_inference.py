# app/analysis/assumption_inference.py

def infer_assumptions(state):
    """
    Infer architectural assumptions with risk levels and mitigation strategies.
    Detects 10+ critical assumptions about the codebase architecture.
    """
    assumptions = []

    layers = state.layers
    metrics = state.graph_metrics
    archetype = state.archetype
    files = getattr(state, 'files', [])
    
    # ---------------------------
    # 1. Backend/Frontend Separation
    # ---------------------------
    if archetype == "frontend" and not layers.get("backend"):
        assumptions.append({
            "assumption": "Backend logic is external to this repository",
            "evidence": {
                "archetype": archetype,
                "backend_layers": False,
                "api_calls_detected": _detect_api_calls(files),
            },
            "impact": "Frontend is tightly coupled to external API contracts",
            "risk_level": "HIGH",
            "confidence": 0.9,
            "mitigation": [
                "Implement API client abstraction layer",
                "Add contract testing (e.g., Pact)",
                "Document API dependencies explicitly",
            ],
        })
    
    # ---------------------------
    # 2. Database Assumptions
    # ---------------------------
    db_evidence = _detect_database_usage(files, layers)
    if db_evidence["has_db_layer"]:
        assumptions.append({
            "assumption": f"Using {db_evidence['db_type']} database without ORM abstraction" 
                         if not db_evidence["has_orm"] 
                         else f"Using {db_evidence['orm_type']} ORM for data access",
            "evidence": {
                "database_type": db_evidence["db_type"],
                "orm_detected": db_evidence["has_orm"],
                "orm_type": db_evidence["orm_type"],
                "migration_files": db_evidence["has_migrations"],
            },
            "impact": "Database schema changes require coordinated updates" 
                     if not db_evidence["has_migrations"] 
                     else "Schema evolution managed through migrations",
            "risk_level": "MEDIUM" if db_evidence["has_migrations"] else "HIGH",
            "confidence": 0.85,
            "mitigation": [
                "Implement database migration strategy",
                "Add integration tests for data layer",
                "Document schema evolution process",
            ] if not db_evidence["has_migrations"] else [
                "Maintain migration rollback scripts",
                "Test migrations in staging environment",
            ],
        })
    
    # ---------------------------
    # 3. State Management
    # ---------------------------
    state_mgmt = _detect_state_management(files, layers)
    if state_mgmt["detected"]:
        assumptions.append({
            "assumption": f"Centralized state management using {state_mgmt['type']}",
            "evidence": {
                "state_manager": state_mgmt["type"],
                "store_files": state_mgmt["store_files"][:3],
                "global_state_files": len(state_mgmt["store_files"]),
            },
            "impact": "State changes can trigger cascade updates across components",
            "risk_level": "MEDIUM",
            "confidence": 0.8,
            "mitigation": [
                "Implement state normalization",
                "Add selectors to prevent unnecessary re-renders",
                "Document state shape and update patterns",
                "Consider state splitting for performance",
            ],
        })
    elif archetype == "frontend" and len(layers.get("ui", [])) > 10:
        assumptions.append({
            "assumption": "No centralized state management detected",
            "evidence": {
                "ui_components": len(layers.get("ui", [])),
                "state_manager": None,
            },
            "impact": "State likely managed via props drilling or local component state",
            "risk_level": "HIGH",
            "confidence": 0.75,
            "mitigation": [
                "Consider adopting Redux, Zustand, or Context API",
                "Audit prop drilling depth",
                "Implement state management for complex flows",
            ],
        })
    
    # ---------------------------
    # 4. Authentication & Authorization
    # ---------------------------
    auth_evidence = _detect_auth_patterns(files, layers)
    if auth_evidence["has_auth"]:
        assumptions.append({
            "assumption": f"Authentication handled via {auth_evidence['auth_type']}",
            "evidence": {
                "auth_type": auth_evidence["auth_type"],
                "auth_files": auth_evidence["auth_files"][:3],
                "middleware_detected": auth_evidence["has_middleware"],
            },
            "impact": "Security model depends on proper auth implementation",
            "risk_level": "CRITICAL",
            "confidence": 0.85,
            "mitigation": [
                "Implement comprehensive auth testing",
                "Add security audit for auth flows",
                "Document authentication requirements",
                "Enable MFA/2FA for sensitive operations",
                "Regular security reviews of auth code",
            ],
        })
    elif archetype in ["backend", "fullstack"]:
        assumptions.append({
            "assumption": "No authentication layer detected",
            "evidence": {
                "auth_files": [],
                "middleware_detected": False,
            },
            "impact": "API endpoints may be unprotected",
            "risk_level": "CRITICAL",
            "confidence": 0.7,
            "mitigation": [
                "URGENT: Implement authentication layer",
                "Add authorization middleware",
                "Audit all endpoints for security",
            ],
        })
    
    # ---------------------------
    # 5. Testing Coverage
    # ---------------------------
    test_evidence = _detect_testing_setup(files, layers)
    if test_evidence["has_tests"]:
        test_ratio = test_evidence["test_files"] / max(len(files), 1)
        risk_level = "LOW" if test_ratio > 0.3 else "MEDIUM" if test_ratio > 0.15 else "HIGH"
        
        assumptions.append({
            "assumption": f"Testing infrastructure present ({test_evidence['test_framework']})",
            "evidence": {
                "test_framework": test_evidence["test_framework"],
                "test_files": test_evidence["test_files"],
                "test_ratio": f"{test_ratio:.1%}",
                "has_e2e": test_evidence["has_e2e"],
                "has_integration": test_evidence["has_integration"],
            },
            "impact": f"Test coverage appears {'adequate' if risk_level == 'LOW' else 'insufficient'}",
            "risk_level": risk_level,
            "confidence": 0.9,
            "mitigation": [
                "Increase test coverage to >80%",
                "Add integration tests for critical paths",
                "Implement E2E tests for user flows",
            ] if risk_level != "LOW" else [
                "Maintain current test coverage",
                "Add mutation testing for quality assurance",
            ],
        })
    else:
        assumptions.append({
            "assumption": "No testing infrastructure detected",
            "evidence": {
                "test_files": 0,
                "test_framework": None,
            },
            "impact": "No automated quality assurance",
            "risk_level": "CRITICAL",
            "confidence": 0.95,
            "mitigation": [
                "URGENT: Set up testing framework (Jest, Pytest, etc.)",
                "Add unit tests for critical logic",
                "Implement CI/CD with test gates",
                "Establish testing guidelines",
            ],
        })
    
    # ---------------------------
    # 6. Deployment & Build Setup
    # ---------------------------
    deploy_evidence = _detect_deployment_setup(files)
    if deploy_evidence["has_config"]:
        assumptions.append({
            "assumption": f"Deployment configured for {deploy_evidence['platform']}",
            "evidence": {
                "platform": deploy_evidence["platform"],
                "config_files": deploy_evidence["config_files"],
                "has_ci": deploy_evidence["has_ci"],
                "containerized": deploy_evidence["containerized"],
            },
            "impact": "Deployment process is codified",
            "risk_level": "LOW" if deploy_evidence["has_ci"] else "MEDIUM",
            "confidence": 0.85,
            "mitigation": [
                "Document deployment process",
                "Add deployment rollback procedures",
                "Implement canary deployments",
            ] if not deploy_evidence["has_ci"] else [
                "Maintain deployment documentation",
                "Regular DR testing",
            ],
        })
    else:
        assumptions.append({
            "assumption": "No deployment configuration detected",
            "evidence": {
                "config_files": [],
                "has_ci": False,
            },
            "impact": "Manual deployment process, high error risk",
            "risk_level": "HIGH",
            "confidence": 0.8,
            "mitigation": [
                "Create deployment configuration",
                "Set up CI/CD pipeline",
                "Document deployment procedures",
                "Implement infrastructure as code",
            ],
        })
    
    # ---------------------------
    # 7. High UI Centrality (Hub Components)
    # ---------------------------
    ui_files = layers.get("ui", [])
    if ui_files and metrics.get("fan_in"):
        high_fan_in_ui = [
            f for f in ui_files
            if metrics["fan_in"].get(f, 0) > 5
        ]

        if high_fan_in_ui:
            max_fan_in = max(metrics["fan_in"].get(f, 0) for f in high_fan_in_ui)
            risk_level = "CRITICAL" if max_fan_in > 15 else "HIGH" if max_fan_in > 10 else "MEDIUM"
            
            assumptions.append({
                "assumption": "UI components act as architectural hubs",
                "evidence": {
                    "high_fan_in_files": high_fan_in_ui[:3],
                    "max_dependencies": max_fan_in,
                    "hub_count": len(high_fan_in_ui),
                },
                "impact": "Changes to shared UI components have wide blast radius",
                "risk_level": risk_level,
                "confidence": 0.8,
                "mitigation": [
                    "Refactor god components into smaller pieces",
                    "Implement component composition patterns",
                    "Add visual regression testing for hub components",
                    "Consider micro-frontend architecture",
                ],
            })
    
    # ---------------------------
    # 8. API/Service Layer Coupling
    # ---------------------------
    if archetype in ["backend", "fullstack"]:
        api_files = layers.get("api", [])
        service_files = layers.get("services", [])
        
        if api_files and service_files:
            coupling_ratio = len(api_files) / max(len(service_files), 1)
            if coupling_ratio > 1.5 or coupling_ratio < 0.5:
                assumptions.append({
                    "assumption": "Imbalanced API to Service layer ratio",
                    "evidence": {
                        "api_files": len(api_files),
                        "service_files": len(service_files),
                        "ratio": f"{coupling_ratio:.2f}",
                    },
                    "impact": "Potential tight coupling between layers" if coupling_ratio > 1.5 
                             else "Business logic may be scattered",
                    "risk_level": "MEDIUM",
                    "confidence": 0.7,
                    "mitigation": [
                        "Audit layer responsibilities",
                        "Refactor to balance API and service logic",
                        "Implement clear layer boundaries",
                        "Add architecture decision records (ADRs)",
                    ],
                })
    
    # ---------------------------
    # 9. Third-party Dependencies
    # ---------------------------
    deps_evidence = _detect_dependency_management(files)
    if deps_evidence["has_lockfile"]:
        assumptions.append({
            "assumption": f"Dependencies managed via {deps_evidence['package_manager']}",
            "evidence": {
                "package_manager": deps_evidence["package_manager"],
                "lockfile": deps_evidence["lockfile"],
                "dependency_count": deps_evidence["dependency_count"],
            },
            "impact": "Reproducible builds enabled",
            "risk_level": "LOW",
            "confidence": 0.95,
            "mitigation": [
                "Regular dependency updates",
                "Security vulnerability scanning",
                "Audit unused dependencies",
            ],
        })
    else:
        assumptions.append({
            "assumption": "No dependency lockfile detected",
            "evidence": {
                "package_manager": deps_evidence["package_manager"],
                "lockfile": None,
            },
            "impact": "Non-reproducible builds, version drift risk",
            "risk_level": "HIGH",
            "confidence": 0.85,
            "mitigation": [
                "Add lockfile (package-lock.json, poetry.lock, etc.)",
                "Commit lockfile to version control",
                "Enable dependency scanning",
            ],
        })
    
    # ---------------------------
    # 10. Error Handling & Logging
    # ---------------------------
    error_evidence = _detect_error_handling(files, layers)
    if error_evidence["has_error_handling"]:
        assumptions.append({
            "assumption": f"Error handling via {error_evidence['error_type']}",
            "evidence": {
                "error_handlers": error_evidence["error_files"][:3],
                "logging_detected": error_evidence["has_logging"],
                "monitoring_detected": error_evidence["has_monitoring"],
            },
            "impact": "Error tracking and recovery mechanisms present",
            "risk_level": "LOW" if error_evidence["has_monitoring"] else "MEDIUM",
            "confidence": 0.75,
            "mitigation": [
                "Implement centralized error logging",
                "Add error monitoring (Sentry, etc.)",
                "Document error recovery procedures",
            ] if not error_evidence["has_monitoring"] else [
                "Maintain error monitoring alerts",
                "Regular error pattern analysis",
            ],
        })
    
    return assumptions


# ---------------------------
# Helper Detection Functions
# ---------------------------

def _detect_api_calls(files):
    """Detect if frontend makes API calls"""
    api_patterns = ['fetch(', 'axios', 'api.', 'http.', 'request(']
    return any(pattern in str(files) for pattern in api_patterns)


def _detect_database_usage(files, layers):
    """Detect database type and ORM usage"""
    evidence = {
        "has_db_layer": False,
        "db_type": None,
        "has_orm": False,
        "orm_type": None,
        "has_migrations": False,
    }
    
    file_str = ' '.join(str(f) for f in files)
    
    # Detect database type
    if 'postgres' in file_str.lower() or 'psycopg' in file_str:
        evidence["db_type"] = "PostgreSQL"
        evidence["has_db_layer"] = True
    elif 'mysql' in file_str.lower() or 'pymysql' in file_str:
        evidence["db_type"] = "MySQL"
        evidence["has_db_layer"] = True
    elif 'mongo' in file_str.lower():
        evidence["db_type"] = "MongoDB"
        evidence["has_db_layer"] = True
    elif 'sqlite' in file_str.lower():
        evidence["db_type"] = "SQLite"
        evidence["has_db_layer"] = True
    
    # Detect ORM
    if 'sqlalchemy' in file_str.lower():
        evidence["has_orm"] = True
        evidence["orm_type"] = "SQLAlchemy"
    elif 'django.db' in file_str:
        evidence["has_orm"] = True
        evidence["orm_type"] = "Django ORM"
    elif 'sequelize' in file_str.lower():
        evidence["has_orm"] = True
        evidence["orm_type"] = "Sequelize"
    elif 'prisma' in file_str.lower():
        evidence["has_orm"] = True
        evidence["orm_type"] = "Prisma"
    
    # Detect migrations
    if any('migration' in str(f).lower() or 'migrate' in str(f).lower() for f in files):
        evidence["has_migrations"] = True
    
    return evidence


def _detect_state_management(files, layers):
    """Detect state management libraries"""
    evidence = {
        "detected": False,
        "type": None,
        "store_files": [],
    }
    
    file_str = ' '.join(str(f) for f in files)
    
    if 'redux' in file_str.lower():
        evidence["detected"] = True
        evidence["type"] = "Redux"
        evidence["store_files"] = [f for f in files if 'store' in str(f).lower() or 'redux' in str(f).lower()]
    elif 'zustand' in file_str.lower():
        evidence["detected"] = True
        evidence["type"] = "Zustand"
        evidence["store_files"] = [f for f in files if 'store' in str(f).lower()]
    elif 'mobx' in file_str.lower():
        evidence["detected"] = True
        evidence["type"] = "MobX"
        evidence["store_files"] = [f for f in files if 'store' in str(f).lower()]
    elif 'recoil' in file_str.lower():
        evidence["detected"] = True
        evidence["type"] = "Recoil"
        evidence["store_files"] = [f for f in files if 'atom' in str(f).lower() or 'recoil' in str(f).lower()]
    elif 'context' in file_str.lower() and 'provider' in file_str.lower():
        evidence["detected"] = True
        evidence["type"] = "React Context"
        evidence["store_files"] = [f for f in files if 'context' in str(f).lower()]
    
    return evidence


def _detect_auth_patterns(files, layers):
    """Detect authentication mechanisms"""
    evidence = {
        "has_auth": False,
        "auth_type": None,
        "auth_files": [],
        "has_middleware": False,
    }
    
    file_str = ' '.join(str(f).lower() for f in files)
    
    if 'jwt' in file_str or 'jsonwebtoken' in file_str:
        evidence["has_auth"] = True
        evidence["auth_type"] = "JWT"
        evidence["auth_files"] = [f for f in files if 'jwt' in str(f).lower() or 'auth' in str(f).lower()]
    elif 'passport' in file_str:
        evidence["has_auth"] = True
        evidence["auth_type"] = "Passport.js"
        evidence["auth_files"] = [f for f in files if 'passport' in str(f).lower() or 'auth' in str(f).lower()]
    elif 'oauth' in file_str:
        evidence["has_auth"] = True
        evidence["auth_type"] = "OAuth"
        evidence["auth_files"] = [f for f in files if 'oauth' in str(f).lower()]
    elif 'firebase' in file_str and 'auth' in file_str:
        evidence["has_auth"] = True
        evidence["auth_type"] = "Firebase Auth"
        evidence["auth_files"] = [f for f in files if 'firebase' in str(f).lower()]
    elif 'auth' in file_str:
        evidence["has_auth"] = True
        evidence["auth_type"] = "Custom Auth"
        evidence["auth_files"] = [f for f in files if 'auth' in str(f).lower()]
    
    if 'middleware' in file_str:
        evidence["has_middleware"] = True
    
    return evidence


def _detect_testing_setup(files, layers):
    """Detect testing framework and coverage"""
    evidence = {
        "has_tests": False,
        "test_framework": None,
        "test_files": 0,
        "has_e2e": False,
        "has_integration": False,
    }
    
    file_str = ' '.join(str(f).lower() for f in files)
    test_files = [f for f in files if any(t in str(f).lower() for t in ['.test.', '.spec.', '_test.', 'test_'])]
    
    evidence["test_files"] = len(test_files)
    
    if test_files:
        evidence["has_tests"] = True
        
        if 'jest' in file_str:
            evidence["test_framework"] = "Jest"
        elif 'pytest' in file_str:
            evidence["test_framework"] = "Pytest"
        elif 'mocha' in file_str:
            evidence["test_framework"] = "Mocha"
        elif 'vitest' in file_str:
            evidence["test_framework"] = "Vitest"
        elif 'unittest' in file_str:
            evidence["test_framework"] = "unittest"
        else:
            evidence["test_framework"] = "Unknown"
        
        if 'cypress' in file_str or 'playwright' in file_str or 'e2e' in file_str:
            evidence["has_e2e"] = True
        
        if 'integration' in file_str:
            evidence["has_integration"] = True
    
    return evidence


def _detect_deployment_setup(files):
    """Detect deployment configuration"""
    evidence = {
        "has_config": False,
        "platform": None,
        "config_files": [],
        "has_ci": False,
        "containerized": False,
    }
    
    file_str = ' '.join(str(f).lower() for f in files)
    
    if 'dockerfile' in file_str or 'docker-compose' in file_str:
        evidence["has_config"] = True
        evidence["containerized"] = True
        evidence["platform"] = "Docker"
        evidence["config_files"].append("Dockerfile")
    
    if 'vercel' in file_str:
        evidence["has_config"] = True
        evidence["platform"] = "Vercel"
        evidence["config_files"].append("vercel.json")
    elif 'netlify' in file_str:
        evidence["has_config"] = True
        evidence["platform"] = "Netlify"
        evidence["config_files"].append("netlify.toml")
    elif 'kubernetes' in file_str or 'k8s' in file_str:
        evidence["has_config"] = True
        evidence["platform"] = "Kubernetes"
        evidence["config_files"].append("k8s configs")
    elif 'terraform' in file_str:
        evidence["has_config"] = True
        evidence["platform"] = "Terraform"
        evidence["config_files"].append("terraform files")
    
    if '.github/workflows' in file_str or 'github' in file_str and 'workflow' in file_str:
        evidence["has_ci"] = True
    elif '.gitlab-ci' in file_str:
        evidence["has_ci"] = True
    elif 'jenkins' in file_str:
        evidence["has_ci"] = True
    elif 'circleci' in file_str:
        evidence["has_ci"] = True
    
    return evidence


def _detect_dependency_management(files):
    """Detect package manager and lockfiles"""
    evidence = {
        "has_lockfile": False,
        "package_manager": None,
        "lockfile": None,
        "dependency_count": 0,
    }
    
    file_str = ' '.join(str(f).lower() for f in files)
    
    if 'package-lock.json' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "npm"
        evidence["lockfile"] = "package-lock.json"
    elif 'yarn.lock' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "yarn"
        evidence["lockfile"] = "yarn.lock"
    elif 'pnpm-lock.yaml' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "pnpm"
        evidence["lockfile"] = "pnpm-lock.yaml"
    elif 'poetry.lock' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "poetry"
        evidence["lockfile"] = "poetry.lock"
    elif 'pipfile.lock' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "pipenv"
        evidence["lockfile"] = "Pipfile.lock"
    elif 'composer.lock' in file_str:
        evidence["has_lockfile"] = True
        evidence["package_manager"] = "composer"
        evidence["lockfile"] = "composer.lock"
    elif 'package.json' in file_str:
        evidence["package_manager"] = "npm/yarn"
    elif 'requirements.txt' in file_str:
        evidence["package_manager"] = "pip"
    
    return evidence


def _detect_error_handling(files, layers):
    """Detect error handling and logging setup"""
    evidence = {
        "has_error_handling": False,
        "error_type": None,
        "error_files": [],
        "has_logging": False,
        "has_monitoring": False,
    }
    
    file_str = ' '.join(str(f).lower() for f in files)
    
    error_files = [f for f in files if 'error' in str(f).lower() or 'exception' in str(f).lower()]
    
    if error_files:
        evidence["has_error_handling"] = True
        evidence["error_files"] = error_files
        evidence["error_type"] = "Custom error handlers"
    
    if 'winston' in file_str or 'bunyan' in file_str:
        evidence["has_logging"] = True
    elif 'logging' in file_str or 'logger' in file_str:
        evidence["has_logging"] = True
    
    if 'sentry' in file_str or 'bugsnag' in file_str or 'rollbar' in file_str:
        evidence["has_monitoring"] = True
    
    return evidence