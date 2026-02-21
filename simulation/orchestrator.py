"""Simulation orchestrator — runs agents through phases and emits events."""

import asyncio
import logging

from agents.definitions import get_agent
from rag.retriever import Retriever
from simulation.events import EventType, SimulationEvent
from simulation.prompts import (
    BUILDING_PROMPTS,
    DEPLOYING_PROMPTS,
    OPERATING_PROMPTS,
    PLANNING_PROMPTS,
    RESEARCH_PROMPTS,
)
from simulation.proposals import extract_proposal_from_response
from simulation.session import Session
from simulation.state import BudgetTracker, Phase, SimulationState, Transaction

logger = logging.getLogger(__name__)

BACKEND_TO_FRONTEND = {
    "product": "product",
    "tech": "tech",
    "finance": "finance",
    "risk": "ops",
    "market": "product",
}

PHASE_AGENTS = {
    Phase.RESEARCHING: ["market", "product", "tech", "finance", "risk"],
    Phase.PLANNING: ["product", "tech", "finance", "risk"],
    Phase.BUILDING: ["tech", "product", "finance", "risk"],
    Phase.DEPLOYING: ["tech", "product", "finance", "risk"],
    Phase.OPERATING: ["market", "product", "tech", "finance", "risk"],
}

PHASE_PROMPTS = {
    Phase.RESEARCHING: RESEARCH_PROMPTS,
    Phase.PLANNING: PLANNING_PROMPTS,
    Phase.BUILDING: BUILDING_PROMPTS,
    Phase.DEPLOYING: DEPLOYING_PROMPTS,
    Phase.OPERATING: OPERATING_PROMPTS,
}

PHASE_ORDER = [Phase.RESEARCHING, Phase.PLANNING, Phase.BUILDING, Phase.DEPLOYING]


async def _run_agent(
    session: Session,
    state: SimulationState,
    bus,
    agent_name: str,
    prompts: dict[str, str],
    retriever: Retriever | None,
    use_rag: bool = False,
) -> bool:
    """Run a single agent: thinking -> prompt -> query -> response -> proposal handling.

    Returns True on success, False if the agent query failed.
    """
    frontend_id = BACKEND_TO_FRONTEND[agent_name]

    await bus.emit(SimulationEvent(
        event_type=EventType.AGENT_THINKING,
        data={"agent_id": frontend_id, "agent_name": agent_name},
    ))

    prompt = _build_prompt(
        prompts.get(agent_name, f"Analyze this idea: {{idea}}"),
        state,
    )

    try:
        agent = get_agent(agent_name, retriever=retriever)
        if use_rag:
            response = await agent.query(
                question=prompt,
                context={"idea": state.idea, "budget": str(state.budget.total)},
            )
        else:
            response = await agent.query_without_rag(
                question=prompt,
                context={"idea": state.idea, "budget": str(state.budget.total)},
            )
    except Exception as e:
        logger.error("Agent %s failed: %s", agent_name, e)
        await bus.emit(SimulationEvent(
            event_type=EventType.ERROR,
            data={"agent_id": frontend_id, "error": str(e)},
        ))
        return False

    state.agent_outputs[f"{agent_name}_{state.phase.value}"] = response.content

    await bus.emit(SimulationEvent(
        event_type=EventType.AGENT_RESPONSE,
        data={
            "agent_id": frontend_id,
            "agent_name": agent_name,
            "content": response.content,
        },
    ))

    proposal = extract_proposal_from_response(response.content, agent_name)
    if proposal:
        if proposal.estimated_cost <= session.auto_approve_threshold:
            approved = state.budget.can_spend(proposal.estimated_cost)
        elif not state.budget.can_spend(proposal.estimated_cost):
            approved = False
        else:
            # Emit PROPOSAL_CREATED and DECISION_NEEDED, then pause for human
            await bus.emit(SimulationEvent(
                event_type=EventType.PROPOSAL_CREATED,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "description": proposal.description,
                    "cost": proposal.estimated_cost,
                    "proposer": agent_name,
                    "agent_id": frontend_id,
                },
            ))
            await bus.emit(SimulationEvent(
                event_type=EventType.DECISION_NEEDED,
                data={
                    "proposal_id": proposal.proposal_id,
                    "title": proposal.title,
                    "cost": proposal.estimated_cost,
                    "agent_id": frontend_id,
                    "agent_name": agent_name,
                    "description": proposal.description,
                },
            ))
            decision = await session.request_decision(proposal, agent_name, state.phase.value)
            approved = decision["approved"]

            await bus.emit(SimulationEvent(
                event_type=EventType.DECISION_MADE,
                data={
                    "proposal_id": proposal.proposal_id,
                    "approved": approved,
                    "reason": decision.get("reason", ""),
                },
            ))

        tx = Transaction(
            agent_id=frontend_id,
            description=proposal.title,
            amount=proposal.estimated_cost,
            approved=approved,
        )
        state.budget.record(tx)

        await bus.emit(SimulationEvent(
            event_type=EventType.BUDGET_UPDATED,
            data={
                "agent_id": frontend_id,
                "description": proposal.title,
                "amount": proposal.estimated_cost,
                "approved": approved,
                "spent": state.budget.spent,
                "total": state.budget.total,
                "remaining": state.budget.remaining,
            },
        ))

    await asyncio.sleep(1.0)
    return True


async def run_simulation(session: Session) -> None:
    """Main orchestrator loop. Runs the simulation to completion."""
    bus = session.event_bus
    state = SimulationState(
        idea=session.idea,
        budget=BudgetTracker(total=session.budget),
    )
    session.state = state
    retriever = _safe_retriever()

    try:
        for phase in PHASE_ORDER:
            state.phase = phase
            await bus.emit(SimulationEvent(
                event_type=EventType.ROUND_STARTED,
                data={"round": phase.value, "stage": phase.value},
            ))

            agents_for_phase = PHASE_AGENTS[phase]
            prompts = PHASE_PROMPTS[phase]
            phase_successes = 0

            for agent_name in agents_for_phase:
                if session.status in ("stopping", "failed"):
                    break
                use_rag = (phase == Phase.RESEARCHING)
                ok = await _run_agent(session, state, bus, agent_name, prompts, retriever, use_rag=use_rag)
                if ok:
                    phase_successes += 1

            if phase_successes == 0 and len(agents_for_phase) > 0:
                # Every agent in this phase failed — abort the simulation
                session.status = "failed"
                await bus.emit(SimulationEvent(
                    event_type=EventType.ERROR,
                    data={"error": "All agents failed. Check your API key and credits.", "fatal": True},
                ))
                break

            await bus.emit(SimulationEvent(
                event_type=EventType.ROUND_COMPLETED,
                data={"round": phase.value},
            ))

        # Enter continuous operations
        state.phase = Phase.OPERATING
        ops_agents = PHASE_AGENTS[Phase.OPERATING]
        ops_prompts = PHASE_PROMPTS[Phase.OPERATING]

        while state.budget.remaining > 0 and session.status not in ("stopping", "failed"):
            state.operations_round += 1
            state.round_label = f"Week {state.operations_round}"

            await bus.emit(SimulationEvent(
                event_type=EventType.ROUND_STARTED,
                data={
                    "round": "operating",
                    "stage": "operating",
                    "ops_round": state.operations_round,
                    "label": state.round_label,
                },
            ))

            ops_successes = 0
            for agent_name in ops_agents:
                if session.status in ("stopping", "failed"):
                    break
                ok = await _run_agent(session, state, bus, agent_name, ops_prompts, retriever, use_rag=False)
                if ok:
                    ops_successes += 1

            if ops_successes == 0:
                session.status = "failed"
                await bus.emit(SimulationEvent(
                    event_type=EventType.ERROR,
                    data={"error": "All agents failed during operations. Check your API key and credits.", "fatal": True},
                ))
                break

            await bus.emit(SimulationEvent(
                event_type=EventType.ROUND_COMPLETED,
                data={"round": "operating", "ops_round": state.operations_round},
            ))
            await asyncio.sleep(2.0)

        state.phase = Phase.COMPLETE
        session.status = "completed"
        await bus.emit(SimulationEvent(
            event_type=EventType.SIMULATION_COMPLETED,
            data={
                "spent": state.budget.spent,
                "remaining": state.budget.remaining,
            },
        ))

    except Exception as e:
        logger.exception("Simulation failed")
        session.status = "failed"
        await bus.emit(SimulationEvent(
            event_type=EventType.ERROR,
            data={"error": str(e), "fatal": True},
        ))
        await bus.emit(SimulationEvent(
            event_type=EventType.SIMULATION_COMPLETED,
            data={"error": str(e)},
        ))


def _safe_retriever() -> Retriever | None:
    """Try to create a Retriever; return None if unavailable."""
    try:
        return Retriever()
    except Exception:
        return None


def _build_prompt(template: str, state: SimulationState) -> str:
    """Fill prompt template with available context from state."""
    tx_lines = "\n".join(
        f"- {t.description}: ${t.amount:.0f} ({'approved' if t.approved else 'blocked'})"
        for t in state.budget.transactions
    ) or "No transactions yet."

    all_outputs = "\n\n".join(
        f"[{key}]:\n{val[:500]}" for key, val in state.agent_outputs.items()
    ) or "No prior outputs."

    replacements = {
        "idea": state.idea,
        "budget": f"{state.budget.total:.0f}",
        "spent": f"{state.budget.spent:.0f}",
        "remaining": f"{state.budget.remaining:.0f}",
        "market_research": state.agent_outputs.get("market_researching", "No market research yet."),
        "product_scope": state.agent_outputs.get("product_planning", "No product scope yet."),
        "tech_progress": state.agent_outputs.get("tech_building", "No tech progress yet."),
        "all_outputs": all_outputs,
        "transactions": tx_lines,
        "ops_round": str(getattr(state, 'operations_round', 0)),
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(f"{{{key}}}", value)
    return result
