import os
import re
from typing import Any, Dict, List, Set

EXCLUDE_DIRS = {
    "node_modules", "venv", ".git", "__pycache__", "dist", "build",
    ".next", "target", ".idea", ".vscode", "env", "bin", "obj",
}

IMPORTANT_FILE_NAMES = {
    "readme.md", "readme", "package.json", "requirements.txt", "pyproject.toml",
    "dockerfile", "docker-compose.yml", "main.py", "app.py", "index.js",
    "index.ts", "server.js", "manage.py", "settings.py", "config.py",
    "go.mod", "pom.xml", "build.gradle",
}

MAX_SUMMARY_CHARS = int(os.environ.get("AI_SUMMARY_MAX_CHARS", "14000"))
MAX_README_CHARS = 2000
MAX_ITEMS = 50


class RepositorySummaryService:
    """Builds compact repository summaries for Gemini — never sends full source code."""

    @staticmethod
    def build_summary(scan_results: Dict[str, Any], source_dir: str) -> Dict[str, Any]:
        parsed = scan_results.get("parsed_data", {})
        folder_tree = RepositorySummaryService._build_folder_tree(source_dir)
        readme_excerpt = RepositorySummaryService._extract_readme(source_dir)
        important_files = RepositorySummaryService._identify_important_files(parsed.get("raw_files", []))

        summary = {
            "file_count": scan_results.get("file_count", 0),
            "folder_count": scan_results.get("folder_count", 0),
            "languages": scan_results.get("languages", {}),
            "tech_stack": scan_results.get("tech_stack", []),
            "folder_structure": folder_tree,
            "readme_excerpt": readme_excerpt,
            "important_files": important_files,
            "code_summaries": RepositorySummaryService._build_code_summaries(parsed),
            "api_routes": RepositorySummaryService._summarize_routes(parsed.get("routes", [])),
            "database_models": list(parsed.get("db_models", []))[:MAX_ITEMS],
            "top_functions": list(parsed.get("functions", []))[:MAX_ITEMS],
            "top_classes": list(parsed.get("classes", []))[:MAX_ITEMS],
            "top_imports": list(parsed.get("imports", []))[:30],
        }
        return RepositorySummaryService._compact_summary(summary)

    @staticmethod
    def to_prompt_text(summary: Dict[str, Any]) -> str:
        """Serialize summary for LLM prompts with token limits."""
        chunks = RepositorySummaryService.chunk_summary(summary)
        return "\n\n".join(chunks)

    @staticmethod
    def chunk_summary(summary: Dict[str, Any]) -> List[str]:
        """Split large summaries into digestible chunks for token optimization."""
        base = {
            "file_count": summary.get("file_count"),
            "folder_count": summary.get("folder_count"),
            "languages": summary.get("languages"),
            "tech_stack": summary.get("tech_stack"),
            "folder_structure": summary.get("folder_structure"),
            "readme_excerpt": summary.get("readme_excerpt"),
            "important_files": summary.get("important_files"),
        }
        chunks = [RepositorySummaryService._json_chunk("Overview", base)]

        code_chunk = {
            "top_functions": summary.get("top_functions", []),
            "top_classes": summary.get("top_classes", []),
            "top_imports": summary.get("top_imports", []),
            "database_models": summary.get("database_models", []),
            "code_summaries": summary.get("code_summaries", []),
        }
        chunks.append(RepositorySummaryService._json_chunk("Code Intelligence", code_chunk))

        api_chunk = {"api_routes": summary.get("api_routes", [])}
        chunks.append(RepositorySummaryService._json_chunk("API Surface", api_chunk))
        return chunks

    @staticmethod
    def _json_chunk(title: str, payload: Dict[str, Any]) -> str:
        import json
        return f"### {title}\n{json.dumps(payload, ensure_ascii=False, indent=2)}"

    @staticmethod
    def _compact_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
        import json
        serialized = json.dumps(summary, ensure_ascii=False)
        if len(serialized) <= MAX_SUMMARY_CHARS:
            return summary

        summary["top_functions"] = summary.get("top_functions", [])[:25]
        summary["top_classes"] = summary.get("top_classes", [])[:25]
        summary["code_summaries"] = summary.get("code_summaries", [])[:15]
        summary["api_routes"] = summary.get("api_routes", [])[:20]
        summary["folder_structure"] = RepositorySummaryService._truncate_tree(
            summary.get("folder_structure", {}), depth=2
        )
        if len(summary.get("readme_excerpt", "")) > MAX_README_CHARS:
            summary["readme_excerpt"] = summary["readme_excerpt"][:MAX_README_CHARS] + "..."
        return summary

    @staticmethod
    def _build_folder_tree(source_dir: str, max_depth: int = 3) -> Dict[str, Any]:
        tree: Dict[str, Any] = {}

        def walk(current: str, node: Dict[str, Any], depth: int) -> None:
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(current))
            except OSError:
                return
            for entry in entries:
                if entry in EXCLUDE_DIRS or entry.startswith("."):
                    continue
                full = os.path.join(current, entry)
                if os.path.isdir(full):
                    child: Dict[str, Any] = {}
                    node[entry + "/"] = child
                    walk(full, child, depth + 1)
                else:
                    if len(node) < 40:
                        node[entry] = "file"

        if os.path.isdir(source_dir):
            walk(source_dir, tree, 0)
        return tree

    @staticmethod
    def _truncate_tree(tree: Dict[str, Any], depth: int) -> Dict[str, Any]:
        if depth <= 0:
            return {"...": "truncated"}
        result = {}
        for key, value in list(tree.items())[:20]:
            if isinstance(value, dict):
                result[key] = RepositorySummaryService._truncate_tree(value, depth - 1)
            else:
                result[key] = value
        return result

    @staticmethod
    def _extract_readme(source_dir: str) -> str:
        candidates = ["README.md", "readme.md", "README", "Readme.md", "README.txt"]
        for name in candidates:
            path = os.path.join(source_dir, name)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(MAX_README_CHARS + 500)
                    content = re.sub(r"\s+", " ", content).strip()
                    return content[:MAX_README_CHARS]
                except OSError:
                    continue
        return ""

    @staticmethod
    def _identify_important_files(raw_files: List[Dict[str, Any]]) -> List[str]:
        important: List[str] = []
        for file_info in raw_files:
            path = file_info.get("path", "")
            base = os.path.basename(path).lower()
            if base in IMPORTANT_FILE_NAMES or any(
                seg in path.lower() for seg in ("routes", "controllers", "models", "services", "api")
            ):
                important.append(path)
            if len(important) >= 30:
                break
        return important

    @staticmethod
    def _build_code_summaries(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Summarize files by metadata only — never include source code."""
        summaries: List[Dict[str, Any]] = []
        raw_files = parsed.get("raw_files", [])
        routes = parsed.get("routes", [])
        routes_by_handler: Dict[str, List[str]] = {}
        for route in routes:
            handler = route.get("handler", "")
            routes_by_handler.setdefault(handler, []).append(
                f"{route.get('method', 'GET')} {route.get('path', '')}"
            )

        for file_info in raw_files[:25]:
            path = file_info.get("path", "")
            name = os.path.splitext(os.path.basename(path))[0]
            related_routes = []
            for handler, route_list in routes_by_handler.items():
                if name.lower() in handler.lower() or handler.lower() in path.lower():
                    related_routes.extend(route_list[:3])
            summaries.append({
                "path": path,
                "lines": file_info.get("lines", 0),
                "extension": file_info.get("ext", ""),
                "related_routes": related_routes[:5],
            })
        return summaries

    @staticmethod
    def _summarize_routes(routes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        result = []
        for route in routes[:MAX_ITEMS]:
            result.append({
                "method": route.get("method", "GET"),
                "path": route.get("path", ""),
                "handler": route.get("handler", ""),
            })
        return result

    @staticmethod
    def fingerprint(scan_results: Dict[str, Any], source_dir: str) -> str:
        """Stable cache key component for a repository."""
        import hashlib
        import json
        parsed = scan_results.get("parsed_data", {})
        payload = {
            "file_count": scan_results.get("file_count"),
            "routes": len(parsed.get("routes", [])),
            "functions": len(parsed.get("functions", [])),
            "classes": len(parsed.get("classes", [])),
            "tech_stack": scan_results.get("tech_stack", []),
            "root": os.path.basename(source_dir.rstrip("/\\")),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
