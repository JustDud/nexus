"""Prompt templates for each simulation phase per agent."""

RESEARCH_PROMPTS: dict[str, str] = {
    "market": (
        "Research the market for this startup idea: {idea}. "
        "Identify TAM/SAM/SOM, target ICP, and top 3 competitors. "
        "Be specific with numbers."
    ),
    "product": (
        "Given this startup idea: {idea}, define the core value proposition "
        "and list 5 potential MVP features ranked by user impact."
    ),
    "tech": (
        "Evaluate technical feasibility for: {idea}. "
        "Recommend a tech stack, estimate infrastructure costs, "
        "and identify technical risks."
    ),
    "finance": (
        "Create an initial budget allocation plan for a ${budget} budget "
        "to build: {idea}. Set spending limits per category."
    ),
    "risk": (
        "Identify the top 5 risks (legal, market, technical, operational) "
        "for this startup: {idea}. Rate each by severity and likelihood."
    ),
}

PLANNING_PROMPTS: dict[str, str] = {
    "product": (
        "Based on this market research:\n{market_research}\n\n"
        "Scope the MVP for: {idea}. List exactly 3 features with user stories "
        "and acceptance criteria.\n\n"
        "If you want to propose spending, include a block like:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "tech": (
        "Based on this product scope:\n{product_scope}\n\n"
        "Design the technical architecture for: {idea}. "
        "Estimate build time and infrastructure costs.\n\n"
        "If you need to purchase tools or services, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "finance": (
        "Review these agent outputs and any spending proposals:\n{all_outputs}\n\n"
        "Current budget: ${budget}, spent so far: ${spent}. "
        "Approve, reduce, or block each proposal. Explain every decision."
    ),
    "risk": (
        "Review the MVP plan and tech architecture:\n{all_outputs}\n\n"
        "Flag any compliance, legal, or operational risks for: {idea}. "
        "Recommend mitigations with cost estimates."
    ),
}

BUILDING_PROMPTS: dict[str, str] = {
    "tech": (
        "Execute the build plan for: {idea}. "
        "Report progress on each feature. Flag any blockers or cost overruns. "
        "Current budget remaining: ${remaining}.\n\n"
        "If you need additional purchases, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "product": (
        "The MVP for {idea} is being built. Review tech progress:\n{tech_progress}\n\n"
        "Adjust priorities if needed. Propose any marketing spend for pre-launch.\n\n"
        "If you want to propose spending, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "finance": (
        "Building phase update for: {idea}. "
        "Spending so far: ${spent} of ${budget}. "
        "Transactions:\n{transactions}\n\n"
        "Flag any burn rate concerns."
    ),
    "risk": (
        "Building phase for: {idea}. "
        "Review technical implementation for security and compliance. "
        "Current state:\n{all_outputs}"
    ),
}

DEPLOYING_PROMPTS: dict[str, str] = {
    "tech": (
        "Deploy the MVP for: {idea}. "
        "Run pre-launch checklist: SSL, DNS, backups, monitoring. "
        "Report status and any issues."
    ),
    "product": (
        "MVP for {idea} is deploying. Prepare launch: "
        "landing page copy, social media posts, waitlist campaign.\n\n"
        "If you want to propose marketing spend, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "finance": (
        "Final budget review for: {idea}. "
        "Total spent: ${spent} of ${budget}. "
        "Generate financial summary and runway projection."
    ),
    "risk": (
        "Pre-launch compliance check for: {idea}. "
        "Verify: privacy policy, terms of service, cookie consent, GDPR. "
        "Report status."
    ),
}

OPERATING_PROMPTS: dict[str, str] = {
    "market": (
        "Operations week {ops_round} for: {idea}. "
        "Budget remaining: ${remaining} of ${budget}. Spent: ${spent}.\n"
        "Transactions so far:\n{transactions}\n\n"
        "Previous outputs:\n{all_outputs}\n\n"
        "Plan and execute marketing campaigns for this week. "
        "Consider paid ads, content marketing, influencer partnerships, "
        "and community building. Report expected reach and conversion metrics.\n\n"
        "If you want to propose marketing spend, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "product": (
        "Operations week {ops_round} for: {idea}. "
        "Budget remaining: ${remaining} of ${budget}. Spent: ${spent}.\n"
        "Previous outputs:\n{all_outputs}\n\n"
        "Review user feedback and product metrics from the live MVP. "
        "Propose feature iterations, UX improvements, or A/B tests "
        "for this week. Prioritize by user impact.\n\n"
        "If you want to propose spending on product improvements, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "tech": (
        "Operations week {ops_round} for: {idea}. "
        "Budget remaining: ${remaining} of ${budget}. Spent: ${spent}.\n"
        "Previous outputs:\n{all_outputs}\n\n"
        "Review server performance, uptime, and infrastructure costs. "
        "Address any scaling needs, security patches, or DevOps improvements. "
        "Report current monthly hosting/API costs.\n\n"
        "If you need to purchase infrastructure or services, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
    "finance": (
        "Operations week {ops_round} for: {idea}. "
        "Budget remaining: ${remaining} of ${budget}. Spent: ${spent}.\n"
        "Transactions:\n{transactions}\n\n"
        "Previous outputs:\n{all_outputs}\n\n"
        "Analyze current burn rate, revenue (if any), and financial runway. "
        "Flag any budget concerns and recommend adjustments. "
        "Project how many more weeks the budget can sustain operations."
    ),
    "risk": (
        "Operations week {ops_round} for: {idea}. "
        "Budget remaining: ${remaining} of ${budget}. Spent: ${spent}.\n"
        "Previous outputs:\n{all_outputs}\n\n"
        "Monitor ongoing compliance, legal exposure, and operational risks. "
        "Check for data privacy incidents, regulatory changes, or SLA breaches. "
        "Report risk status and recommend mitigations.\n\n"
        "If you need to propose compliance or risk mitigation spending, include:\n"
        "[PROPOSAL]\nTitle: short name\nCost: $amount\n"
        "Description: what and why\n[/PROPOSAL]"
    ),
}
