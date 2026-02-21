"""Prompt templates for each simulation phase."""


def research_prompt(startup_idea: str) -> str:
    return f"""\
Analyze the following startup idea as a market research specialist.

Startup idea: {startup_idea}

Provide a thorough analysis covering:
1. **Market size** — TAM, SAM, SOM estimates with reasoning
2. **Target segments** — primary and secondary customer segments, their pain points
3. **Competitors** — direct and indirect competitors, their strengths/weaknesses
4. **Timing** — why now? What trends or shifts make this viable today?

Cite your sources wherever possible. Reference specific data points, reports, or known market dynamics.

End with a clear **Recommendation**: proceed, pivot, or abandon — and why."""


def mvp_proposal_prompt(startup_idea: str, market_research: str) -> str:
    return f"""\
Based on the market research below, propose a Minimum Viable Product for this startup.

Startup idea: {startup_idea}

Market research summary:
{market_research}

Your proposal must include:
1. **Value proposition** — one clear sentence
2. **Core features** — 3 to 5 features for the MVP, prioritized
3. **Explicit exclusions** — what is NOT in the MVP and why
4. **Target persona** — the single most important early adopter
5. **Success metrics** — measurable KPIs for validating the MVP

For any spending required, use these markers on separate lines:
PROPOSAL: <what you want to spend on>
COST: <amount in dollars>
CATEGORY: <engineering | marketing | infrastructure | operations>
REASON: <why this spend is necessary>"""


def feasibility_review_prompt(mvp_proposal: str) -> str:
    return f"""\
Evaluate the technical feasibility of this MVP proposal.

MVP proposal:
{mvp_proposal}

Provide:
1. **Complexity assessment** — rate each proposed feature as low / medium / high complexity
2. **Recommended tech stack** — languages, frameworks, services, and why
3. **Build time estimate** — realistic timeline for a small team (2-4 engineers)
4. **Technical risks** — what could go wrong, dependencies, scaling concerns

For any infrastructure or tooling spend, use these markers on separate lines:
PROPOSAL: <what you want to spend on>
COST: <amount in dollars>
CATEGORY: <engineering | marketing | infrastructure | operations>
REASON: <why this spend is necessary>"""


def budget_review_prompt(proposals_text: str, budget_remaining: float) -> str:
    return f"""\
Review the following spending proposals as the finance advisor.

Proposals:
{proposals_text}

Remaining budget: ${budget_remaining:,.2f}

For EACH proposal, provide your vote using these markers on separate lines:
VOTE: SUPPORT | OPPOSE | CONDITIONAL
REASONING: <your financial reasoning>
CONDITIONS: <conditions that must be met, if CONDITIONAL>

After reviewing each proposal individually, provide:
- **Total proposed spend** vs remaining budget
- **Runway impact** — how these expenditures affect the startup's runway
- **Priority ranking** — if budget is tight, which proposals to fund first"""


def risk_review_prompt(proposals_text: str, startup_idea: str) -> str:
    return f"""\
Assess risks for the following proposals in the context of this startup.

Startup idea: {startup_idea}

Proposals:
{proposals_text}

Evaluate:
1. **Legal risks** — regulatory compliance, licensing, liability
2. **Privacy risks** — data handling, GDPR/CCPA concerns, user consent
3. **Competitive risks** — how competitors might respond, moat durability
4. **Operational risks** — team capacity, vendor dependencies, single points of failure
5. **IP risks** — patent exposure, trade secret concerns, open source licensing

If any proposal needs modifications to manage risk, use these markers:
VOTE: SUPPORT | OPPOSE | CONDITIONAL
REASONING: <your risk reasoning>
CONDITIONS: <required risk mitigations, if CONDITIONAL>"""


def debate_response_prompt(
    agent_name: str,
    prior_messages: str,
    topic: str,
) -> str:
    return f"""\
You are {agent_name}. Respond to the ongoing debate about: {topic}

Prior discussion:
{prior_messages}

Provide your response in 2-4 paragraphs. Be direct and substantive. You may agree, disagree, or propose alternatives. Reference specific points from prior messages.

If you want to propose new spending or modify existing proposals, use:
PROPOSAL: <what>
COST: <amount>
CATEGORY: <category>
REASON: <why>

If you want to vote on an existing proposal, use:
VOTE: SUPPORT | OPPOSE | CONDITIONAL
REASONING: <your reasoning>
CONDITIONS: <conditions, if any>"""
