"""Optimized prompts for SaaSMiner AI intelligence engines."""

SYSTEM_CONTEXT = (
    "You are SaaSMiner AI, a senior software architect and startup strategist. "
    "Analyze repository summaries to identify SaaS productization opportunities. "
    "Respond ONLY with valid JSON matching the requested schema. "
    "Never include markdown fences or commentary outside JSON."
)

DOMAIN_DETECTION_PROMPT = """Analyze this repository summary and classify its primary business domain.

Repository Summary:
{summary}

Return JSON:
{{
  "domain": "<one of: Healthcare, Education, Finance & Banking, E-Commerce & Retail, Logistics & Inventory, Human Resources, Enterprise CRM & Sales, Generic SaaS Utility>",
  "confidence": <float 0-100>,
  "reasoning": "<2-4 sentences explaining classification>",
  "description": "<one sentence domain description>"
}}"""

MODULE_DETECTION_PROMPT = """Identify business modules in this repository based on file structure, naming, and code summaries.

Repository Summary:
{summary}

Return JSON:
{{
  "modules": [
    {{
      "name": "<module name>",
      "confidence": <int 40-98>,
      "description": "<what this module does>",
      "features": ["<feature 1>", "<feature 2>"],
      "matched_indicators": ["<evidence from repo>"],
      "files": ["<relevant file paths, max 5>"]
    }}
  ]
}}

Identify 2-8 modules. Include Authentication or Billing only if evidence exists."""

PRODUCT_SCORE_PROMPT = """Evaluate this repository's SaaS productization potential.

Repository Summary:
{summary}

Detected Domain: {domain}
Detected Modules: {modules}

Return JSON:
{{
  "overall_score": <int 20-99>,
  "category_scores": {{
    "saas_viability": <int 0-100>,
    "market_fit": <int 0-100>,
    "scalability": <int 0-100>,
    "uniqueness": <int 0-100>,
    "monetization_potential": <int 0-100>,
    "technical_maturity": <int 0-100>
  }},
  "reasoning": "<3-5 sentences with specific evidence from the repository>"
}}"""

SAAS_RECOMMENDATION_PROMPT = """Generate SaaS transformation recommendations for this repository.

Repository Summary:
{summary}

Domain: {domain} (confidence: {confidence}%)
Overall Score: {score}/100
Modules: {modules}

Return JSON:
{{
  "recommended_product": "<product name>",
  "product_type": "<SaaS Product | API Product | Enterprise Software | Internal Developer Tool>",
  "explanation": "<why this product type fits>",
  "can_become_product": "<YES or NO>",
  "target_customers": ["<customer segment>"],
  "pricing_suggestions": ["<pricing idea>"],
  "subscription_models": ["<model>"],
  "roadmap": ["<step 1>", "<step 2>", "<step 3>", "<step 4>"],
  "reasons": ["<reason 1>", "<reason 2>", "<reason 3>"]
}}"""

BUSINESS_OPPORTUNITY_PROMPT = """Analyze business opportunities for productizing this repository.

Repository Summary:
{summary}

Domain: {domain}
Product Score: {score}/100
SaaS Recommendation: {saas_rec}

Return JSON:
{{
  "target_market": "<primary market>",
  "potential_customers": "<customer profiles>",
  "estimated_market_size": "<TAM estimate with context>",
  "tam_estimate": "<numeric TAM range e.g. $500M-$2B>",
  "monetization": "<primary monetization approach>",
  "monetization_strategy": "<detailed strategy>",
  "key_selling_points": ["<point 1>", "<point 2>", "<point 3>"],
  "market_opportunities": ["<opportunity 1>", "<opportunity 2>"],
  "competitor_categories": ["<category 1>", "<category 2>"],
  "growth_strategy": "<2-3 sentence growth plan>",
  "business_potential": "<High | Medium to High | Medium | Low>",
  "rationale": "<why this opportunity exists>"
}}"""

MICROSERVICE_PROMPT = """Propose a microservice architecture for this repository.

Repository Summary:
{summary}

Domain: {domain}
Modules: {modules}
API Routes: {apis}

Return JSON:
{{
  "services": [
    {{
      "name": "<service name>",
      "tech_stack": "<recommended stack>",
      "database": "<database>",
      "responsibilities": ["<responsibility>"],
      "dependencies": ["<dependency service names>"]
    }}
  ],
  "relationships": [
    {{"from": "<service>", "to": "<service>", "type": "HTTP/gRPC"}}
  ],
  "proposed_apis": [
    {{"path": "<route>", "method": "<HTTP method>", "service": "<owning service>", "description": "<purpose>"}}
  ],
  "deployment_strategy": "<cloud-native deployment approach>",
  "rationale": "<why this decomposition fits>"
}}

Always include API Gateway and Authentication Service."""

ARCHITECTURE_PROMPT = """Generate architecture documentation for this microservice proposal.

Microservice Proposal:
{microservices}

Domain: {domain}

Return JSON:
{{
  "mermaid_diagram": "<valid mermaid flowchart TD diagram as a single string with \\n for newlines>",
  "component_descriptions": [
    {{"component": "<name>", "description": "<role and responsibilities>"}}
  ],
  "deployment_architecture": "<describe containers, orchestration, CI/CD, and cloud layout>"
}}"""
