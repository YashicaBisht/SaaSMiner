from typing import Dict, List, Any
import json

from .ai_prompts import SAAS_RECOMMENDATION_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService


class SaaSRecommender:
    @staticmethod
    def recommend(
        scanner_results: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any],
        score_info: Dict[str, Any],
        repo_summary: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return AIService.run_with_fallback(
            lambda: SaaSRecommender._recommend_with_ai(
                repo_summary or {}, detected_modules, domain_info, score_info
            ),
            lambda: SaaSRecommender._recommend_rule_based(
                scanner_results, detected_modules, domain_info, score_info
            ),
        )

    @staticmethod
    def _recommend_with_ai(
        repo_summary: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any],
        score_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        from .repository_summary_service import RepositorySummaryService

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        module_names = [m.get("name", "") for m in detected_modules]
        prompt = f"{SYSTEM_CONTEXT}\n\n{SAAS_RECOMMENDATION_PROMPT.format(
            summary=summary_text,
            domain=domain_info.get('domain', 'Unknown'),
            confidence=domain_info.get('confidence', 70),
            score=score_info.get('overall_score', 50),
            modules=json.dumps(module_names),
        )}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            data.setdefault("target_customers", [])
            data.setdefault("pricing_suggestions", [])
            data.setdefault("subscription_models", [])
            data.setdefault("roadmap", [])
            data.setdefault("reasons", [])
            can = str(data.get("can_become_product", "YES")).upper()
            data["can_become_product"] = "YES" if can.startswith("Y") else "NO"
            return data

        return AIService.generate_json(
            prompt,
            namespace="saas_recommendation",
            cache_payload=f"{summary_text}:{score_info.get('overall_score')}",
            required_fields=[
                "recommended_product", "product_type", "explanation",
                "can_become_product", "roadmap", "reasons",
            ],
            validator=validate,
        )

    @staticmethod
    def _recommend_rule_based(
        scanner_results: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any],
        score_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        overall_score = score_info.get("overall_score", 50)
        domain = domain_info.get("domain", "Generic Utility")

        has_auth = any(m["name"] == "Authentication" for m in detected_modules)
        has_billing = any(
            "billing" in m["name"].lower() or "payment" in m["name"].lower()
            for m in detected_modules
        )
        route_count = len(scanner_results.get("parsed_data", {}).get("routes", []))

        if overall_score >= 80 and has_billing:
            product_type = "SaaS Product"
            explanation = "Excellent modular structure combined with transaction models. Ready for multi-tenant subscription."
        elif overall_score >= 70 and route_count > 10:
            product_type = "API Product"
            explanation = "Substantial backend route coverage. Reusable as an API-first microservice or headless service."
        elif overall_score >= 60:
            product_type = "Enterprise Software"
            explanation = "Strong business logical cores. Suitable for on-premise installation or private cloud deployments."
        else:
            product_type = "Internal Developer Tool"
            explanation = "Valuable utility features. Best deployed internally as an efficiency booster before scaling."

        clean_domain = domain.split("&")[0].strip()
        if product_type == "SaaS Product":
            recommended_name = f"Cloud{clean_domain} Pro SaaS"
        elif product_type == "API Product":
            recommended_name = f"{clean_domain}Core Engine API"
        elif product_type == "Enterprise Software":
            recommended_name = f"{clean_domain}Suite Enterprise"
        else:
            recommended_name = f"Local{clean_domain} Toolkit"

        roadmap = [
            "Implement multi-tenant database partitioning to safely segregate customer records.",
            "Refactor current inline authorization blocks into standard Middleware guards."
        ]

        if not has_auth:
            roadmap.insert(0, "Add OAuth2/JWT secure authentication layers to control endpoint accessibility.")
        if not has_billing:
            roadmap.append("Integrate billing gateways (e.g. Stripe checkout) for subscription and tier control.")
        else:
            roadmap.append("Add credit card usage analytics and automatic invoicing models.")

        roadmap.append("Set up Docker containers and CI/CD pipelines to build scalable cloud-native micro-clusters.")

        return {
            "recommended_product": recommended_name,
            "product_type": product_type,
            "explanation": explanation,
            "can_become_product": "YES" if overall_score >= 50 else "NO",
            "target_customers": [f"{domain} startups and SMBs"],
            "pricing_suggestions": ["Tiered monthly subscription", "Usage-based API pricing"],
            "subscription_models": ["Freemium", "Pro", "Enterprise"],
            "roadmap": roadmap,
            "reasons": [
                f"Matches {domain} indicators with {domain_info.get('confidence')}% confidence.",
                f"Scored {overall_score}/100 on product modularity and reusability.",
                f"Discovered {len(detected_modules)} core business modules in scanner.",
                f"Identified {route_count} functional endpoints ready for external access."
            ]
        }
