from typing import Dict, Any
import json

from .ai_prompts import BUSINESS_OPPORTUNITY_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService

DOMAIN_BUSINESS_TEMPLATES = {
    "Healthcare": {
        "target_market": "Hospitals, Private Practices, and Digital Health Startups.",
        "potential_customers": "Outpatient clinics, regional hospitals, specialized practitioners, telehealth software operators.",
        "estimated_market_size": "$350B Global Digital Health Market",
        "tam_estimate": "$300B-$400B",
        "monetization": "Per-provider monthly subscriptions (SaaS), payment transaction fees (1-2%), or enterprise self-hosted licensing.",
        "key_selling_points": [
            "HIPAA-compliant patient record architecture.",
            "Automated scheduling reduces staff coordination overhead by 30%.",
            "Extensible API for connecting to custom diagnostic systems."
        ],
        "business_potential": "High"
    },
    "Education": {
        "target_market": "K-12 Schools, Academic Universities, and Corporate Learning Centers.",
        "potential_customers": "Charter schools, code bootcamps, online course authors, employee training agencies.",
        "estimated_market_size": "$280B Global EdTech Market",
        "tam_estimate": "$250B-$300B",
        "monetization": "Per-student monthly active licenses, premium content course-split fees, or school-district broad contracts.",
        "key_selling_points": [
            "Modular syllabus pacing structure.",
            "Online submissions and interactive grading pipelines minimize grading times.",
            "Teacher-parent communication and enrollment automation."
        ],
        "business_potential": "Medium to High"
    },
    "Finance & Banking": {
        "target_market": "FinTech startups, Microfinance agencies, and Neo-banks.",
        "potential_customers": "Local credit unions, personal budget startups, retail payment facilitators.",
        "estimated_market_size": "$620B Global FinTech Market",
        "tam_estimate": "$500B-$700B",
        "monetization": "Per-transaction micro-fees, credit screening api charges, or white-labeled banking ledger licenses.",
        "key_selling_points": [
            "Sleek transaction ledger architecture.",
            "Extensible cards and wallets model API.",
            "Instant micro-transfer routing interfaces."
        ],
        "business_potential": "High"
    },
    "E-Commerce & Retail": {
        "target_market": "Online Merchants, Direct-To-Consumer (D2C) brands, and Warehouse distributors.",
        "potential_customers": "Boutique Shopify sellers, multi-channel wholesalers, niche e-commerce founders.",
        "estimated_market_size": "$5.7T Global Retail E-commerce Market",
        "tam_estimate": "$1T-$6T",
        "monetization": "Per-transaction checkout revenue share, monthly inventory sync limits, or custom theme licensing.",
        "key_selling_points": [
            "Superfast, headless catalog loading.",
            "Automated multi-warehouse stock decrementing.",
            "Integrates stripe checkout workflows instantly out of the box."
        ],
        "business_potential": "High"
    },
    "Logistics & Inventory": {
        "target_market": "Supply chain operators, Freight forwarders, and Delivery networks.",
        "potential_customers": "Third-party logistics (3PL) providers, local courier fleets, small wholesale warehouses.",
        "estimated_market_size": "$12.8T Global Logistics Market",
        "tam_estimate": "$10B-$50B addressable SaaS segment",
        "monetization": "Per-vehicle active tracker routing licenses, monthly order dispatch caps, or enterprise fleet systems.",
        "key_selling_points": [
            "Optimized courier dispatch pipelines.",
            "Live package tracking updates and API hooks.",
            "Structured inventory warehouse space management systems."
        ],
        "business_potential": "Medium"
    },
    "Human Resources": {
        "target_market": "Mid-sized SMBs, Professional recruitment agencies, and Staffing providers.",
        "potential_customers": "Growth startups (50-500 employees), contract hiring firms, payroll consulting firms.",
        "estimated_market_size": "$38B Global HR Tech Market",
        "tam_estimate": "$30B-$45B",
        "monetization": "Per-employee seat licenses, recruiter pipeline tracking fees, or flat-rate payroll engine access.",
        "key_selling_points": [
            "Centralized timesheet and vacation approval queues.",
            "Recruiter pipeline and candidate scoring profiles.",
            "Secure corporate payroll ledgers."
        ],
        "business_potential": "Medium"
    },
    "Generic SaaS Utility": {
        "target_market": "Indie hackers, developer agencies, and digital product studios.",
        "potential_customers": "Solopreneurs, internal development groups, project architects.",
        "estimated_market_size": "$190B Global Developer Tools Market",
        "tam_estimate": "$150B-$220B",
        "monetization": "Open-source core with paid hosting options, API key usage limits, or custom extension licenses.",
        "key_selling_points": [
            "Extremely clean, modern stack scaffolding.",
            "Instant JWT session setups.",
            "Interactive configuration dashboard UI."
        ],
        "business_potential": "Medium"
    }
}


class BusinessOpportunityEngine:
    @staticmethod
    def analyze(
        domain: str,
        overall_score: int,
        repo_summary: Dict[str, Any] = None,
        saas_rec: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return AIService.run_with_fallback(
            lambda: BusinessOpportunityEngine._analyze_with_ai(
                repo_summary or {}, domain, overall_score, saas_rec or {}
            ),
            lambda: BusinessOpportunityEngine._analyze_rule_based(domain, overall_score),
        )

    @staticmethod
    def _analyze_with_ai(
        repo_summary: Dict[str, Any],
        domain: str,
        overall_score: int,
        saas_rec: Dict[str, Any],
    ) -> Dict[str, Any]:
        from .repository_summary_service import RepositorySummaryService

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        prompt = f"{SYSTEM_CONTEXT}\n\n{BUSINESS_OPPORTUNITY_PROMPT.format(
            summary=summary_text,
            domain=domain,
            score=overall_score,
            saas_rec=json.dumps(saas_rec),
        )}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            data.setdefault("tam_estimate", data.get("estimated_market_size", "N/A"))
            data.setdefault("market_opportunities", [])
            data.setdefault("competitor_categories", [])
            data.setdefault("monetization_strategy", data.get("monetization", ""))
            data.setdefault("growth_strategy", "")
            data.setdefault("key_selling_points", [])
            return data

        return AIService.generate_json(
            prompt,
            namespace="business_opportunity",
            cache_payload=f"{summary_text}:{domain}:{overall_score}",
            required_fields=[
                "target_market", "potential_customers", "estimated_market_size",
                "monetization", "key_selling_points", "business_potential", "rationale",
            ],
            validator=validate,
        )

    @staticmethod
    def _analyze_rule_based(domain: str, overall_score: int) -> Dict[str, Any]:
        domain_key = "Generic SaaS Utility"
        for k in DOMAIN_BUSINESS_TEMPLATES.keys():
            if k.split()[0] in domain:
                domain_key = k
                break

        template = DOMAIN_BUSINESS_TEMPLATES[domain_key]

        pot = template["business_potential"]
        if overall_score < 55:
            pot = "Medium"
        elif overall_score < 40:
            pot = "Low"

        return {
            "target_market": template["target_market"],
            "potential_customers": template["potential_customers"],
            "estimated_market_size": template["estimated_market_size"],
            "tam_estimate": template.get("tam_estimate", template["estimated_market_size"]),
            "monetization": template["monetization"],
            "monetization_strategy": template["monetization"],
            "key_selling_points": template["key_selling_points"],
            "market_opportunities": [
                f"Vertical SaaS expansion in {domain_key}",
                "API monetization for integrators and partners",
            ],
            "competitor_categories": [
                f"Established {domain_key} incumbents",
                "Horizontal workflow automation platforms",
            ],
            "growth_strategy": "Land with a focused niche wedge, expand via integrations, then upsell enterprise tiers.",
            "business_potential": pot,
            "rationale": (
                "The project's architectural structure is strong enough to address these markets "
                "directly with minor enhancements. Target monetization fits modern subscription frameworks."
            ),
        }
