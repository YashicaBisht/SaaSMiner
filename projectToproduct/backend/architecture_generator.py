from typing import Dict, List, Any
import json

from .ai_prompts import ARCHITECTURE_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService


class ArchitectureGenerator:
    @staticmethod
    def generate_diagram(
        microservice_proposal: Dict[str, Any],
        domain: str = "Generic SaaS Utility",
    ) -> Dict[str, Any]:
        react_flow = ArchitectureGenerator._build_react_flow(microservice_proposal)

        ai_metadata = AIService.run_with_fallback(
            lambda: ArchitectureGenerator._generate_ai_metadata(microservice_proposal, domain),
            lambda: ArchitectureGenerator._default_ai_metadata(microservice_proposal),
        )

        return {
            **react_flow,
            "mermaid_diagram": ai_metadata.get("mermaid_diagram", ""),
            "component_descriptions": ai_metadata.get("component_descriptions", []),
            "deployment_architecture": ai_metadata.get("deployment_architecture", ""),
        }

    @staticmethod
    def _generate_ai_metadata(
        microservice_proposal: Dict[str, Any],
        domain: str,
    ) -> Dict[str, Any]:
        prompt = f"{SYSTEM_CONTEXT}\n\n{ARCHITECTURE_PROMPT.format(
            microservices=json.dumps(microservice_proposal),
            domain=domain,
        )}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            data.setdefault("mermaid_diagram", "")
            data.setdefault("component_descriptions", [])
            data.setdefault("deployment_architecture", "")
            return data

        return AIService.generate_json(
            prompt,
            namespace="architecture_metadata",
            cache_payload=json.dumps(microservice_proposal.get("services", [])),
            required_fields=["mermaid_diagram", "component_descriptions", "deployment_architecture"],
            validator=validate,
        )

    @staticmethod
    def _default_ai_metadata(microservice_proposal: Dict[str, Any]) -> Dict[str, Any]:
        services = microservice_proposal.get("services", [])
        nodes = ["Frontend[React Frontend] --> Gateway[API Gateway]"]
        for svc in services:
            if svc["name"] == "API Gateway":
                continue
            sid = svc["name"].replace(" ", "_")
            nodes.append(f"Gateway --> {sid}[{svc['name']}]")
        return {
            "mermaid_diagram": "flowchart TD\n    " + "\n    ".join(nodes),
            "component_descriptions": [
                {"component": s["name"], "description": ", ".join(s.get("responsibilities", []))}
                for s in services[:8]
            ],
            "deployment_architecture": microservice_proposal.get(
                "deployment_strategy",
                "Containerized microservices behind an API gateway with managed databases.",
            ),
        }

    @staticmethod
    def _build_react_flow(microservice_proposal: Dict[str, Any]) -> Dict[str, Any]:
        services = microservice_proposal.get("services", [])

        nodes = []
        edges = []

        nodes.append({
            "id": "frontend",
            "type": "customNode",
            "position": {"x": 50, "y": 250},
            "data": {
                "label": "React Frontend",
                "subtitle": "Vite + TailwindCSS",
                "category": "frontend",
                "icon": "layout"
            }
        })

        nodes.append({
            "id": "gateway",
            "type": "customNode",
            "position": {"x": 250, "y": 250},
            "data": {
                "label": "API Gateway",
                "subtitle": "Reverse Proxy & Rate Limit",
                "category": "gateway",
                "icon": "shuffle"
            }
        })

        edges.append({
            "id": "e-front-gate",
            "source": "frontend",
            "target": "gateway",
            "animated": True,
            "style": {"stroke": "#8b5cf6", "strokeWidth": 2}
        })

        service_idx = 0

        for service in services:
            name = service["name"]
            if name == "API Gateway":
                continue

            node_id = name.lower().replace(" ", "_").replace("&", "and")

            x = 480
            y = 80 + (service_idx * 130)
            service_idx += 1

            is_auth = "auth" in node_id or "authentication" in node_id
            category = "auth" if is_auth else "service"
            icon = "shield" if is_auth else "cpu"

            nodes.append({
                "id": node_id,
                "type": "customNode",
                "position": {"x": x, "y": y},
                "data": {
                    "label": name,
                    "subtitle": service["tech_stack"],
                    "category": category,
                    "icon": icon
                }
            })

            edges.append({
                "id": f"e-gate-{node_id}",
                "source": "gateway",
                "target": node_id,
                "animated": True,
                "style": {"stroke": "#3b82f6", "strokeWidth": 1.5}
            })

            db_name = service["database"]
            if db_name:
                db_id = f"db_{node_id}"
                db_x = 750
                db_y = y - 10

                is_third_party = "stripe" in db_name.lower() or "paypal" in db_name.lower()
                db_category = "thirdparty" if is_third_party else "database"
                db_icon = "external-link" if is_third_party else "database"

                nodes.append({
                    "id": db_id,
                    "type": "customNode",
                    "position": {"x": db_x, "y": db_y},
                    "data": {
                        "label": db_name.split(" (")[0],
                        "subtitle": db_name.split(" (")[-1].replace(")", "") if " (" in db_name else db_name,
                        "category": db_category,
                        "icon": db_icon
                    }
                })

                edges.append({
                    "id": f"e-{node_id}-{db_id}",
                    "source": node_id,
                    "target": db_id,
                    "style": {"stroke": "#10b981", "strokeDasharray": "5 5", "strokeWidth": 1.5}
                })

                if not is_auth and any("auth" in n["id"] for n in nodes):
                    auth_node_id = [n["id"] for n in nodes if "auth" in n["id"]][0]
                    edges.append({
                        "id": f"e-{auth_node_id}-{node_id}",
                        "source": auth_node_id,
                        "target": node_id,
                        "style": {"stroke": "#cbd5e1", "strokeWidth": 1, "opacity": 0.6}
                    })

        return {
            "nodes": nodes,
            "edges": edges
        }
