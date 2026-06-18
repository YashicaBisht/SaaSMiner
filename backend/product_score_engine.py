from typing import Dict, List, Any

from .ai_prompts import PRODUCT_SCORE_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService

CATEGORY_TO_BREAKDOWN = {
    "saas_viability": "modularity",
    "market_fit": "market_applicability",
    "scalability": "scalability",
    "uniqueness": "reusability",
    "monetization_potential": "business_value",
    "technical_maturity": "architecture_quality",
}


class ProductScoreEngine:
    @staticmethod
    def calculate_score(
        scanner_results: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any],
        repo_summary: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return AIService.run_with_fallback(
            lambda: ProductScoreEngine._score_with_ai(
                repo_summary or {}, detected_modules, domain_info
            ),
            lambda: ProductScoreEngine._score_rule_based(
                scanner_results, detected_modules, domain_info
            ),
        )

    @staticmethod
    def _score_with_ai(
        repo_summary: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        from .repository_summary_service import RepositorySummaryService
        import json

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        module_names = [m.get("name", "") for m in detected_modules]
        prompt = f"{SYSTEM_CONTEXT}\n\n{PRODUCT_SCORE_PROMPT.format(
            summary=summary_text,
            domain=domain_info.get('domain', 'Unknown'),
            modules=json.dumps(module_names),
        )}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            overall = int(data.get("overall_score", 50))
            data["overall_score"] = max(20, min(overall, 99))
            category_scores = data.get("category_scores", {})
            breakdown = {}
            for ai_key, legacy_key in CATEGORY_TO_BREAKDOWN.items():
                breakdown[legacy_key] = max(0, min(int(category_scores.get(ai_key, 50)), 100))
            data["category_scores"] = {
                k: max(0, min(int(v), 100)) for k, v in category_scores.items()
            }
            data["breakdown"] = breakdown
            data.setdefault("reasoning", "AI-evaluated productization potential.")
            return data

        return AIService.generate_json(
            prompt,
            namespace="product_score",
            cache_payload=f"{summary_text}:{domain_info.get('domain')}",
            required_fields=["overall_score", "category_scores", "reasoning"],
            validator=validate,
        )

    @staticmethod
    def _score_rule_based(
        scanner_results: Dict[str, Any],
        detected_modules: List[Dict[str, Any]],
        domain_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        parsed_data = scanner_results.get("parsed_data", {})

        file_count = scanner_results.get("file_count", 0)
        func_count = len(parsed_data.get("functions", []))
        class_count = len(parsed_data.get("classes", []))
        db_model_count = len(parsed_data.get("db_models", []))
        route_count = len(parsed_data.get("routes", []))
        module_count = len(detected_modules)

        modularity = 50
        if file_count > 0:
            density = (func_count + class_count) / file_count
            if 2 <= density <= 15:
                modularity += 30
            elif density > 15:
                modularity += 15
            else:
                modularity += 10
        modularity += min(module_count * 5, 20)
        modularity = min(modularity, 100)

        reusability = 60
        reusability += min(class_count * 2, 20)
        has_utils = any(
            "util" in f["path"].lower() or "helper" in f["path"].lower()
            for f in parsed_data.get("raw_files", [])
        )
        if has_utils:
            reusability += 15
        reusability = min(reusability, 100)

        scalability = 45
        scalability += min(db_model_count * 5, 25)
        scalability += min(route_count * 3, 25)
        has_docker = any("docker" in f.lower() for f in scanner_results.get("tech_stack", []))
        if has_docker:
            scalability += 10
        scalability = min(scalability, 100)

        architecture_quality = 55
        if route_count > 0 and db_model_count > 0:
            architecture_quality += 20
        if scanner_results.get("folder_count", 0) > 4:
            architecture_quality += 15
        architecture_quality = min(architecture_quality, 100)

        business_value = 50
        has_billing = any(
            "billing" in m["name"].lower() or "payment" in m["name"].lower()
            for m in detected_modules
        )
        has_crm = any("crm" in m["name"].lower() for m in detected_modules)
        if has_billing:
            business_value += 25
        if has_crm:
            business_value += 15
        business_value += int(domain_info.get("confidence", 70) * 0.15)
        business_value = min(business_value, 100)

        market_applicability = 65
        popular_domains = [
            "Healthcare", "Finance & Banking", "E-Commerce & Retail", "Enterprise CRM & Sales"
        ]
        if domain_info.get("domain") in popular_domains:
            market_applicability += 15
        market_applicability += min(route_count, 15)
        market_applicability = min(market_applicability, 100)

        composite_score = int(
            (modularity + reusability + scalability + architecture_quality + business_value + market_applicability) / 6
        )
        composite_score = max(min(composite_score, 99), 20)

        breakdown = {
            "modularity": modularity,
            "reusability": reusability,
            "scalability": scalability,
            "architecture_quality": architecture_quality,
            "business_value": business_value,
            "market_applicability": market_applicability,
        }

        return {
            "overall_score": composite_score,
            "breakdown": breakdown,
            "category_scores": {
                "saas_viability": modularity,
                "market_fit": market_applicability,
                "scalability": scalability,
                "uniqueness": reusability,
                "monetization_potential": business_value,
                "technical_maturity": architecture_quality,
            },
            "reasoning": "Rule-based scoring from repository structure, modules, and domain confidence.",
        }
