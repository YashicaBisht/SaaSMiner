from typing import Dict, Any
import re

from .ai_prompts import DOMAIN_DETECTION_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService

DOMAIN_RULES = {
    "Healthcare": {
        "keywords": [r"patient", r"appointment", r"medical", r"doctor", r"health", r"clinic", r"hospital", r"prescription", r"diagnos", r"ehr", r"emr"],
        "description": "Clinical operations, patient scheduling, medical histories, and digital healthcare platforms."
    },
    "Education": {
        "keywords": [r"course", r"student", r"teacher", r"school", r"classroom", r"grade", r"exam", r"assignment", r"lesson", r"curriculum", r"enroll"],
        "description": "LMS (Learning Management Systems), student tracking, curriculum pacing, and class scheduling."
    },
    "Finance & Banking": {
        "keywords": [r"bank", r"transaction", r"transfer", r"credit", r"debit", r"loan", r"balance", r"ledger", r"deposit", r"wallet", r"payment", r"invoice", r"crypto", r"portfolio"],
        "description": "Digital ledger accounting, transaction records, fund transfers, wallet platforms, and microfinance services."
    },
    "E-Commerce & Retail": {
        "keywords": [r"product", r"cart", r"checkout", r"store", r"order", r"sku", r"shop", r"purchase", r"catalog", r"coupon", r"discount", r"shipping", r"inventory"],
        "description": "Retail storefront operations, checkout flows, digital carts, inventory catalogs, and product tracking."
    },
    "Logistics & Inventory": {
        "keywords": [r"shipment", r"warehouse", r"transit", r"delivery", r"courier", r"package", r"tracking", r"fleet", r"dispatch", r"consignment", r"carrier"],
        "description": "Cargo movements, package routing, carrier dispatch systems, and warehouse logistics."
    },
    "Human Resources": {
        "keywords": [r"employee", r"payroll", r"attendance", r"leave", r"vacation", r"candidate", r"hiring", r"resume", r"appraisal", r"timesheet", r"salary"],
        "description": "Personnel profiles, attendance systems, employee payrolls, leave approvals, and recruitment pipelines."
    },
    "Enterprise CRM & Sales": {
        "keywords": [r"crm", r"lead", r"opportunity", r"sales", r"pipeline", r"contact", r"prospect", r"deal", r"interaction", r"customer_success"],
        "description": "Customer lifecycle trackers, sales funnel visualizers, client interaction logs, and pipeline CRM systems."
    }
}

VALID_DOMAINS = list(DOMAIN_RULES.keys()) + ["Generic SaaS Utility"]


class DomainDetector:
    @staticmethod
    def detect_domain(
        scanner_results: Dict[str, Any],
        repo_summary: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return AIService.run_with_fallback(
            lambda: DomainDetector._detect_with_ai(repo_summary or {}),
            lambda: DomainDetector._detect_rule_based(scanner_results),
        )

    @staticmethod
    def _detect_with_ai(repo_summary: Dict[str, Any]) -> Dict[str, Any]:
        from .repository_summary_service import RepositorySummaryService

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        prompt = f"{SYSTEM_CONTEXT}\n\n{DOMAIN_DETECTION_PROMPT.format(summary=summary_text)}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            domain = data.get("domain", "Generic SaaS Utility")
            if domain not in VALID_DOMAINS:
                data["domain"] = "Generic SaaS Utility"
            confidence = float(data.get("confidence", 70))
            data["confidence"] = max(0.0, min(confidence, 100.0))
            data["matched_terms"] = ["ai_analysis"]
            data.setdefault("description", "AI-classified domain based on repository structure and semantics.")
            data.setdefault("reasoning", data.get("description", ""))
            return data

        return AIService.generate_json(
            prompt,
            namespace="domain_detection",
            cache_payload=summary_text,
            required_fields=["domain", "confidence", "reasoning"],
            validator=validate,
        )

    @staticmethod
    def _detect_rule_based(scanner_results: Dict[str, Any]) -> Dict[str, Any]:
        parsed_data = scanner_results.get("parsed_data", {})

        funcs = " ".join(parsed_data.get("functions", []))
        classes = " ".join(parsed_data.get("classes", []))
        db_models = " ".join(parsed_data.get("db_models", []))
        routes = " ".join([r.get("path", "") for r in parsed_data.get("routes", [])])
        files = " ".join([f.get("path", "") for f in parsed_data.get("raw_files", [])])

        search_blob = (funcs + " " + classes + " " + db_models + " " + routes + " " + files).lower()

        domain_scores = {}
        for domain, rules in DOMAIN_RULES.items():
            matches = []
            for kw in rules["keywords"]:
                count = len(re.findall(kw, search_blob))
                if count > 0:
                    matches.append((kw, count))

            if matches:
                distinct_matches = len(matches)
                total_freq = sum(c for _, c in matches)
                score = (distinct_matches * 15) + min(total_freq * 2, 45)
                domain_scores[domain] = {
                    "score": min(score, 100),
                    "matched_terms": [m[0] for m in matches],
                    "description": rules["description"]
                }

        if not domain_scores:
            return {
                "domain": "Generic SaaS Utility",
                "confidence": 70.0,
                "matched_terms": ["generic"],
                "description": "Universal software structure. Configured as a base utility or general-purpose platform.",
                "reasoning": "No strong domain keywords detected; classified as a general-purpose utility.",
            }

        best_domain = max(domain_scores, key=lambda k: domain_scores[k]["score"])
        best_data = domain_scores[best_domain]
        confidence = float(min(75 + int(best_data["score"] * 0.24), 98))

        return {
            "domain": best_domain,
            "confidence": confidence,
            "matched_terms": best_data["matched_terms"],
            "description": best_data["description"],
            "reasoning": f"Rule-based classification matched {len(best_data['matched_terms'])} domain indicators for {best_domain}.",
        }
