"""Simulation orchestrator — drives the startup simulation through all phases."""

from __future__ import annotations

import asyncio

from agents.base import BaseAgent
from agents.definitions import get_agent
from rag.retriever import Retriever
from simulation.debate import DebateManager
import logging

from simulation.events import (
    AGENT_THINKING,
    BUDGET_UPDATED,
    EventType,
    PHASE_CHANGED,
    PROPOSAL_EXECUTED,
    SIMULATION_COMPLETED,
    SIMULATION_STARTED,
    EventBus,
    SimulationEvent,
)

logger = logging.getLogger(__name__)
from simulation.prompts import (
    budget_review_prompt,
    feasibility_review_prompt,
    mvp_proposal_prompt,
    research_prompt,
    risk_review_prompt,
)
from simulation.proposals import (
    Proposal,
    ProposalStatus,
    extract_proposal_from_response,
    extract_vote_from_response,
)
from simulation.state import Phase, SimulationState

_BUDGET_WARNING_THRESHOLD = 0.20  # 20% remaining triggers warning

# Map backend agent names to frontend agent IDs
_FRONTEND_ID = {
    "market": "product",
    "product": "product",
    "tech": "tech",
    "finance": "finance",
    "risk": "ops",
}


class SimulationOrchestrator:
    """Drives the simulation through research → proposal → debate → decision → execution."""

    def __init__(self, state: SimulationState, event_bus: EventBus) -> None:
        self.state = state
        self.event_bus = event_bus
        self._retriever = Retriever()
        self.agents: dict[str, BaseAgent] = {
            name: get_agent(name, retriever=self._retriever)
            for name in ("market", "product", "tech", "finance", "risk")
        }

    async def _emit_thinking(self, agent_name: str, task: str) -> None:
        """Emit AGENT_THINKING so the frontend shows activity."""
        fid = _FRONTEND_ID.get(agent_name, "tech")
        await self.event_bus.emit(SimulationEvent(
            event_type=EventType.AGENT_THINKING,
            data={"agent_id": fid, "agent_name": agent_name.title(), "task": task},
        ))

    async def _emit_response(self, agent_name: str, content: str) -> None:
        """Emit AGENT_RESPONSE so the frontend sees the result."""
        fid = _FRONTEND_ID.get(agent_name, "tech")
        await self.event_bus.emit(SimulationEvent(
            event_type=EventType.AGENT_RESPONSE,
            data={"agent_id": fid, "agent_name": agent_name.title(), "content": content},
        ))

    async def start(self, idea: str, budget: float) -> None:
        """Initialize the simulation and emit startup events."""
        self.state.initialize(idea, budget)
        await self.event_bus.emit(SIMULATION_STARTED, {
            "idea": idea,
            "budget": budget,
            "simulation_id": self.state.id,
        })
        await self.event_bus.emit(BUDGET_UPDATED, {
            "remaining": self.state.budget.remaining,
            "initial": self.state.initial_budget,
            "total_spent": 0.0,
        })

    async def run_until_decision(self) -> None:
        """Run phases sequentially until we reach DECISION, COMPLETED, or FAILED."""
        terminal = {Phase.DECISION, Phase.COMPLETED, Phase.FAILED}
        while self.state.phase not in terminal:
            await self._run_current_phase()
            # Check budget after each phase
            if self.state.budget.remaining <= 0 and self.state.phase not in terminal:
                self.state.phase = Phase.FAILED
                await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.FAILED)})

    async def _run_current_phase(self) -> None:
        """Dispatch to the handler for the current phase."""
        handlers = {
            Phase.RESEARCH: self._run_research,
            Phase.PROPOSAL: self._run_proposal,
            Phase.DEBATE: self._run_debate,
            Phase.EXECUTION: self._run_execution,
        }
        handler = handlers.get(self.state.phase)
        if handler:
            await handler()

    # ------------------------------------------------------------------
    # Phase handlers
    # ------------------------------------------------------------------

    async def _run_research(self) -> None:
        """Market Agent researches the idea using RAG retrieval."""
        agent = self.agents["market"]
        prompt = research_prompt(self.state.startup_idea)
        context = self.state.get_context_dict()

        await self._emit_thinking("market", "Researching market opportunity")
        response = await agent.query(prompt, context=context)
        await self._emit_response("market", response.content)

        self.state.add_message(
            agent=response.agent,
            role=response.role,
            content=response.content,
            phase=Phase.RESEARCH,
            citations=response.citations,
        )

        self.state.completed_phases.append(str(Phase.RESEARCH))
        self.state.phase = Phase.PROPOSAL
        await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.PROPOSAL)})

    async def _run_proposal(self) -> None:
        """Chain: Product → Tech → Finance → Risk.

        Each agent receives the full conversation so far (via state.get_context_dict()),
        so every agent sees what all prior agents have said across all phases.
        The prompts provide the specific task; the conversation provides full context.
        """
        proposals: list[Proposal] = []

        # Product Agent — MVP proposal (sees research via conversation)
        product_agent = self.agents["product"]
        product_prompt = mvp_proposal_prompt(self.state.startup_idea)
        await self._emit_thinking("product", "Designing MVP proposal")
        product_resp = await product_agent.query_without_rag(
            product_prompt, context=self.state.get_context_dict(),
        )
        await self._emit_response("product", product_resp.content)
        self.state.add_message(
            agent=product_resp.agent, role=product_resp.role,
            content=product_resp.content, phase=Phase.PROPOSAL,
            citations=product_resp.citations,
        )
        p = extract_proposal_from_response(product_resp.content, product_resp.agent)
        if p:
            proposals.append(p)

        # Tech Agent — feasibility review (sees research + product via conversation)
        tech_agent = self.agents["tech"]
        tech_prompt = feasibility_review_prompt()
        await self._emit_thinking("tech", "Reviewing technical feasibility")
        tech_resp = await tech_agent.query_without_rag(
            tech_prompt, context=self.state.get_context_dict(),
        )
        await self._emit_response("tech", tech_resp.content)
        self.state.add_message(
            agent=tech_resp.agent, role=tech_resp.role,
            content=tech_resp.content, phase=Phase.PROPOSAL,
            citations=tech_resp.citations,
        )
        p = extract_proposal_from_response(tech_resp.content, tech_resp.agent)
        if p:
            proposals.append(p)

        # Finance Agent — budget review (sees everything so far via conversation)
        finance_agent = self.agents["finance"]
        proposals_text = "\n\n".join(
            f"- {pr.title} | Cost: {pr.estimated_cost} | Category: {pr.category}"
            for pr in proposals
        ) or "(No spending proposals yet.)"
        finance_prompt = budget_review_prompt(proposals_text, self.state.budget.remaining)
        await self._emit_thinking("finance", "Reviewing budget allocation")
        finance_resp = await finance_agent.query_without_rag(
            finance_prompt, context=self.state.get_context_dict(),
        )
        await self._emit_response("finance", finance_resp.content)
        self.state.add_message(
            agent=finance_resp.agent, role=finance_resp.role,
            content=finance_resp.content, phase=Phase.PROPOSAL,
            citations=finance_resp.citations,
        )
        vote = extract_vote_from_response(finance_resp.content, finance_resp.agent)
        if vote:
            for pr in proposals:
                pr.votes.append(vote)

        # Risk Agent — risk review (sees everything so far via conversation)
        risk_agent = self.agents["risk"]
        risk_prompt = risk_review_prompt(proposals_text, self.state.startup_idea)
        await self._emit_thinking("risk", "Assessing risks and mitigation strategies")
        risk_resp = await risk_agent.query_without_rag(
            risk_prompt, context=self.state.get_context_dict(),
        )
        await self._emit_response("risk", risk_resp.content)
        self.state.add_message(
            agent=risk_resp.agent, role=risk_resp.role,
            content=risk_resp.content, phase=Phase.PROPOSAL,
            citations=risk_resp.citations,
        )
        vote = extract_vote_from_response(risk_resp.content, risk_resp.agent)
        if vote:
            for pr in proposals:
                pr.votes.append(vote)

        self.state.pending_proposals = proposals
        self.state.completed_phases.append(str(Phase.PROPOSAL))
        self.state.phase = Phase.DEBATE
        await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.DEBATE)})

    async def _run_debate(self) -> None:
        """Run the debate manager, then route results."""
        dm = DebateManager(self.agents, self.state, self.event_bus)
        proposals = await dm.run_debate(
            topic=self.state.startup_idea,
            initial_proposals=self.state.pending_proposals,
            max_rounds=self.state.max_debate_rounds,
        )

        consensus = [p for p in proposals if p.status == ProposalStatus.APPROVED]
        escalated = [p for p in proposals if p.status != ProposalStatus.APPROVED and p.status != ProposalStatus.REJECTED]

        self.state.decided_proposals.extend(consensus)
        self.state.completed_phases.append(str(Phase.DEBATE))

        if escalated:
            self.state.pending_proposals = escalated
            self.state.phase = Phase.DECISION
            await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.DECISION)})
        else:
            self.state.pending_proposals = []
            self.state.phase = Phase.EXECUTION
            await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.EXECUTION)})

    async def _run_execution(self) -> None:
        """Execute all approved proposals, then mark completed."""
        for proposal in self.state.decided_proposals:
            if proposal.status == ProposalStatus.APPROVED:
                await self._execute_proposal(proposal)

        self.state.completed_phases.append(str(Phase.EXECUTION))
        self.state.phase = Phase.COMPLETED
        await self.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.COMPLETED)})

    # ------------------------------------------------------------------
    # CEO decision resolution
    # ------------------------------------------------------------------

    async def resolve_ceo_decision(
        self, proposal_id: str, approved: bool, note: str = ""
    ) -> None:
        """CEO approves or rejects a pending proposal."""
        target = None
        for p in self.state.pending_proposals:
            if p.id == proposal_id:
                target = p
                break

        if target is None:
            return

        if approved:
            target.status = ProposalStatus.APPROVED
            await self._execute_proposal(target)
            self.state.decided_proposals.append(target)
        else:
            target.status = ProposalStatus.REJECTED
            self.state.decided_proposals.append(target)

        self.state.pending_proposals = [
            p for p in self.state.pending_proposals if p.id != proposal_id
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _execute_proposal(self, proposal: Proposal) -> None:
        """Deduct cost from budget, record transaction, check warnings."""
        # Parse cost string to float (e.g. "$1,500" -> 1500.0)
        cost_str = proposal.estimated_cost.replace("$", "").replace(",", "")
        try:
            cost = float(cost_str)
        except ValueError:
            cost = 0.0

        if cost > 0:
            self.state.budget.record(
                description=proposal.title,
                amount=-cost,
                approved_by="CEO",
                category=proposal.category,
            )

        proposal.status = ProposalStatus.EXECUTED

        await self.event_bus.emit(BUDGET_UPDATED, {
            "remaining": self.state.budget.remaining,
            "initial": self.state.initial_budget,
            "total_spent": self.state.budget.total_spent,
        })
        await self.event_bus.emit(PROPOSAL_EXECUTED, {
            "proposal_id": proposal.id,
            "title": proposal.title,
            "cost": cost,
        })

        # 20% warning threshold
        if self.state.budget.remaining <= self.state.initial_budget * _BUDGET_WARNING_THRESHOLD:
            await self.event_bus.emit(BUDGET_UPDATED, {
                "remaining": self.state.budget.remaining,
                "initial": self.state.initial_budget,
                "total_spent": self.state.budget.total_spent,
                "warning": "Budget below 20% threshold",
            })


# ---------------------------------------------------------------------------
# Module-level entry point (used by ws_routes and simulation_routes)
# ---------------------------------------------------------------------------


async def run_simulation(session) -> None:
    """Run the full simulation lifecycle on a session.

    Loops through phases: RESEARCH → PROPOSAL → DEBATE → DECISION → EXECUTION.
    When DECISION is reached, emits DECISION_NEEDED events one at a time and
    waits for CEO input before continuing to EXECUTION.
    """
    try:
        await session.orchestrator.start(session.idea, session.budget)

        while True:
            await session.orchestrator.run_until_decision()

            if session.state.phase == Phase.DECISION:
                session.status = "paused"

                # Present each escalated proposal to the CEO one at a time
                while session.state.pending_proposals:
                    proposal = session.state.pending_proposals[0]
                    cost_str = proposal.estimated_cost.replace("$", "").replace(",", "")
                    try:
                        cost = float(cost_str)
                    except ValueError:
                        cost = 0.0

                    session._current_proposal_id = proposal.id
                    await session.event_bus.emit(SimulationEvent(
                        event_type=EventType.DECISION_NEEDED,
                        data={
                            "proposal_id": proposal.id,
                            "title": proposal.title,
                            "cost": cost,
                            "description": proposal.description,
                            "agent_id": "finance",
                            "agent_name": proposal.proposed_by.title(),
                        },
                    ))

                    # Poll until this proposal is resolved or simulation stopped
                    while any(p.id == proposal.id for p in session.state.pending_proposals):
                        await asyncio.sleep(0.3)
                        if session.status == "stopping":
                            break

                    if session.status == "stopping":
                        break

                    # Notify frontend the decision was made
                    target = next(
                        (p for p in session.state.decided_proposals if p.id == proposal.id),
                        None,
                    )
                    await session.event_bus.emit(SimulationEvent(
                        event_type=EventType.DECISION_MADE,
                        data={
                            "proposal_id": proposal.id,
                            "approved": target.status == ProposalStatus.APPROVED if target else False,
                        },
                    ))

                if session.status == "stopping":
                    session.status = "failed"
                    break

                # All decisions resolved — proceed to execution
                session.status = "running"
                session.state.phase = Phase.EXECUTION
                await session.event_bus.emit(PHASE_CHANGED, {"phase": str(Phase.EXECUTION)})

            elif session.state.phase in (Phase.COMPLETED, Phase.FAILED):
                session.status = session.state.phase.value.lower()
                break
            else:
                break

    except asyncio.CancelledError:
        logger.info("Simulation stopped by user")
        session.status = "stopped"
    except Exception as e:
        logger.exception("Simulation failed: %s", e)
        session.status = "failed"
        await session.event_bus.emit(SimulationEvent(
            event_type=EventType.ERROR,
            data={"error": str(e), "fatal": True},
        ))
    finally:
        # Always emit SIMULATION_COMPLETED so _send_loop exits cleanly
        await session.event_bus.emit(SimulationEvent(
            event_type=EventType.SIMULATION_COMPLETED,
            data={
                "status": session.status or "completed",
                "total_spent": session.state.budget.total_spent,
                "remaining": session.state.budget.remaining,
            },
        ))
