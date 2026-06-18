from typing import Dict, List, Any
import re

from .ai_prompts import MODULE_DETECTION_PROMPT, SYSTEM_CONTEXT
from .ai_service import AIService

MODULE_RULES = {
    "Authentication": {
        "keywords": [r"\blogin\b", r"\bsignup\b", r"\bregister\b", r"\bauth\b", r"\bjwt\b", r"\btoken\b", r"\bpassword\b", r"\bpassport\b", r"\boauth\b"],
        "description": "User login, registration, and session control systems.",
        "features": ["Password Hashing", "JWT Generation", "User Sign-up Flow"]
    },
    "Authorization": {
        "keywords": [r"\brbac\b", r"\bpermission\b", r"\brole\b", r"\bscopes\b", r"\bpolicy\b", r"\bauthorize\b", r"\bis_admin\b", r"\bguard\b"],
        "description": "Role-based access control and action validation permissions.",
        "features": ["Role Mapping", "Access Guards", "Resource Permissions"]
    },
    "Billing & Payments": {
        "keywords": [r"\bstripe\b", r"\bpaypal\b", r"\binvoice\b", r"\bbilling\b", r"\bsubscription\b", r"\bcheckout\b", r"\bpricing\b", r"\bpayment\b", r"\btransaction\b"],
        "description": "Subscription handling, pricing tables, and checkout gateways.",
        "features": ["Payment Gateway Integrations", "Invoice Generation", "Subcription Management"]
    },
    "Notifications": {
        "keywords": [r"\bemail\b", r"\bsms\b", r"\bnotification\b", r"\bsend_mail\b", r"\btwilio\b", r"\bnodemailer\b", r"\bsendgrid\b", r"\bpush\b", r"\bmail\b"],
        "description": "Dispatches alerts, system notifications, or transactional emails.",
        "features": ["Transactional Emailing", "SMS Alerts", "Web Push Notifications"]
    },
    "Analytics & Dashboards": {
        "keywords": [r"\banalytics\b", r"\btracking\b", r"\bmixpanel\b", r"\bsegment\b", r"\blog_event\b", r"\bchart\b", r"\bmetric\b", r"\bdashboard\b"],
        "description": "Visual aggregates, user metrics, and operational charting.",
        "features": ["Activity Logging", "Metric Summarization", "Data Visualizations"]
    },
    "Reporting Engine": {
        "keywords": [r"\breport\b", r"\bexport\b", r"\bpdf\b", r"\bexcel\b", r"\bcsv\b", r"\bxlsx\b", r"\breportlab\b", r"\bdownload_report\b"],
        "description": "Formats, generates, and processes downloadable data reports.",
        "features": ["PDF Exporters", "CSV/Spreadsheet generation", "Data Aggregations"]
    },
    "Customer Relationship Management (CRM)": {
        "keywords": [r"\bcustomer\b", r"\blead\b", r"\bcontact\b", r"\bcrm\b", r"\bdeal\b", r"\binteraction\b", r"\bopportunity\b"],
        "description": "Tracks target customer touchpoints and sales pipelines.",
        "features": ["Lead Tracking", "Contact Histories", "Account Overviews"]
    },
    "User & Workspace Management": {
        "keywords": [r"\buser\b", r"\bprofile\b", r"\bmember\b", r"\bworkspace\b", r"\bteam\b", r"\baccount\b", r"\borg\b", r"\borganization\b"],
        "description": "User profiles, avatars, team setup, and workspace invites.",
        "features": ["Profile Modification", "Team Organization", "Workspace Provisioning"]
    }
}


class ModuleDetector:
    @staticmethod
    def detect_modules(
        scanner_results: Dict[str, Any],
        repo_summary: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        return AIService.run_with_fallback(
            lambda: ModuleDetector._detect_with_ai(repo_summary or {}),
            lambda: ModuleDetector._detect_rule_based(scanner_results),
        )

    @staticmethod
    def _detect_with_ai(repo_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .repository_summary_service import RepositorySummaryService

        summary_text = RepositorySummaryService.to_prompt_text(repo_summary)
        prompt = f"{SYSTEM_CONTEXT}\n\n{MODULE_DETECTION_PROMPT.format(summary=summary_text)}"

        def validate(data: Dict[str, Any]) -> Dict[str, Any]:
            modules = data.get("modules", [])
            if not isinstance(modules, list) or not modules:
                raise ValueError("AI returned no modules")
            normalized = []
            for mod in modules[:8]:
                normalized.append({
                    "name": mod.get("name", "Unknown Module"),
                    "confidence": max(40, min(int(mod.get("confidence", 75)), 98)),
                    "matched_indicators": mod.get("matched_indicators", ["ai_analysis"])[:10],
                    "description": mod.get("description", ""),
                    "features": mod.get("features", [])[:6],
                    "files": mod.get("files", [])[:5],
                })
            return {"modules": normalized}

        result = AIService.generate_json(
            prompt,
            namespace="module_detection",
            cache_payload=summary_text,
            required_fields=["modules"],
            validator=validate,
        )
        return result["modules"]

    @staticmethod
    def _detect_rule_based(scanner_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        parsed_data = scanner_results.get("parsed_data", {})

        functions_str = " ".join(parsed_data.get("functions", []))
        classes_str = " ".join(parsed_data.get("classes", []))
        imports_str = " ".join(parsed_data.get("imports", []))

        routes_list = [r.get("path", "") + " " + r.get("handler", "") for r in parsed_data.get("routes", [])]
        routes_str = " ".join(routes_list)

        files_str = " ".join([f.get("path", "") for f in parsed_data.get("raw_files", [])])

        search_blob = (functions_str + " " + classes_str + " " + imports_str +
                       " " + routes_str + " " + files_str).lower()

        detected_modules = []

        for module_name, rules in MODULE_RULES.items():
            matched_keywords = []

            for keyword in rules["keywords"]:
                if re.search(keyword, search_blob):
                    matched_keywords.append(keyword.replace(r"\b", ""))

            if matched_keywords:
                match_count = len(matched_keywords)
                total_keywords = len(rules["keywords"])
                confidence = min(40 + int((match_count / total_keywords) * 60), 98)

                matching_files = []
                for file_info in parsed_data.get("raw_files", []):
                    file_path_lower = file_info["path"].lower()
                    for keyword in rules["keywords"]:
                        kw_clean = keyword.replace(r"\b", "")
                        if kw_clean in file_path_lower:
                            matching_files.append(file_info["path"])
                            break

                detected_modules.append({
                    "name": module_name,
                    "confidence": confidence,
                    "matched_indicators": matched_keywords,
                    "description": rules["description"],
                    "features": rules["features"],
                    "files": matching_files[:5]
                })

        if not detected_modules:
            detected_modules.append({
                "name": "User & Workspace Management",
                "confidence": 75,
                "matched_indicators": ["user", "settings"],
                "description": "User profiles, settings, and workspace details.",
                "features": ["Profile Configuration"],
                "files": []
            })

        return detected_modules
