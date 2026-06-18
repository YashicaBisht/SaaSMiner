from typing import Dict, List, Any
import json

from .ai_prompts import MICROSERVICE_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService


class MicroserviceEngine:
    @staticmethod
    def propose_microservices(
        detected_modules: List[Dict[str, Any]],
        domain: str,
        repo_summary: Dict[str, Any] = None,
        apis: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return AIService.run_with_fallback(
            lambda: MicroserviceEngine._propose_with_ai(
                repo_summary or {}, detected_modules, domain, apis or []
            ),
            lambda: MicroserviceEngine._propose_rule_based(detected_modules, domain),
        )

    @staticmethod
    def _propose_with_ai(
        repo_summary: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain: str,
        apis: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        from .repository_summary_service import RepositorySummaryService

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        module_names = [m.get("name", "") for m in detected_modules]
        api_sample = apis[:20] if apis else repo_summary.get("api_routes", [])[:20]

        prompt = f"{SYSTEM_CONTEXT}\n\n{MICROSERVICE_PROMPT.format(
            summary=summary_text,
            domain=domain,
            modules=json.dumps(module_names),
            apis=json.dumps(api_sample),
        )}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            services = data.get("services", [])
            if not services:
                raise ValueError("AI returned no microservices")
            data.setdefault("relationships", [])
            data.setdefault("proposed_apis", [])
            data.setdefault("deployment_strategy", "Containerized services on Kubernetes with managed databases.")
            data.setdefault("rationale", "")
            return data

        return AIService.generate_json(
            prompt,
            namespace="microservice_proposal",
            cache_payload=f"{summary_text}:{domain}",
            required_fields=["services", "relationships", "rationale"],
            validator=validate,
        )

    @staticmethod
    def _propose_rule_based(
        detected_modules: List[Dict[str, Any]],
        domain: str
    ) -> Dict[str, Any]:
        services = []

        services.append({
            "name": "API Gateway",
            "tech_stack": "NGINX / Node.js Proxy",
            "database": "Redis (Caching)",
            "responsibilities": [
                "Route request payloads to appropriate downstream micro-nodes.",
                "Enforce global rate limiting and SSL decryption rules."
            ],
            "dependencies": []
        })

        services.append({
            "name": "Authentication Service",
            "tech_stack": "Go / Gin & JWT",
            "database": "PostgreSQL (Users & Auth Tokens)",
            "responsibilities": [
                "Issue, refresh, and validate JSON Web Tokens.",
                "Manage user authentication schemas and MFA structures."
            ],
            "dependencies": ["API Gateway"]
        })

        for module in detected_modules:
            name = module["name"]
            if name in ["Authentication", "Authorization", "User & Workspace Management"]:
                continue

            service_name = f"{name.split('&')[0].strip()} Service"
            tech = "Python / FastAPI"
            db = f"SQLite / PostgreSQL ({name.split('&')[0].strip().lower()}_db)"

            if "Billing" in name or "Payment" in name:
                tech = "Node.js / NestJS"
                db = "PostgreSQL (Ledgers & Billing)"
            elif "Analytics" in name:
                tech = "Go / ClickHouse"
                db = "ClickHouse (Time-series logs)"

            services.append({
                "name": service_name,
                "tech_stack": tech,
                "database": db,
                "responsibilities": [
                    f"Isolate modules relating to {name}.",
                    f"Handle specialized event queues and API transactions for {name.lower()} logic."
                ],
                "dependencies": ["API Gateway", "Authentication Service"]
            })

        if len(services) <= 2:
            clean_domain = domain.split("&")[0].strip()
            services.append({
                "name": f"{clean_domain} Core Service",
                "tech_stack": "Python / FastAPI",
                "database": "PostgreSQL (Core Domain Data)",
                "responsibilities": [
                    f"Manages core business workflows for {clean_domain}.",
                    "Houses domain logic, entities, and primary databases."
                ],
                "dependencies": ["API Gateway", "Authentication Service"]
            })

        edges = []
        for service in services:
            for dep in service["dependencies"]:
                edges.append({
                    "from": dep,
                    "to": service["name"],
                    "type": "HTTP/gRPC"
                })

        return {
            "services": services,
            "relationships": edges,
            "proposed_apis": [],
            "deployment_strategy": (
                "Deploy services as Docker containers behind an API gateway. "
                "Use managed PostgreSQL per service and Redis for caching."
            ),
            "rationale": (
                f"Decomposing the {domain} project into bounded contexts using domain-driven design guidelines. "
                "Each service is fully decoupled, supporting independent deployment schedules."
            )
        }
