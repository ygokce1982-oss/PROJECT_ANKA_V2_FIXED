from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import AgentResult
from .orchestrator import MultiAIOrchestrator


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    role: str
    task_template: str
    required: bool = True


@dataclass(frozen=True)
class WorkflowResult:
    success: bool
    step_results: tuple[AgentResult, ...]
    final_output: str | None = None
    errors: tuple[str, ...] = ()


class MultiAIWorkflow:
    """Sıralı yapay zekâ iş akışı yöneticisi."""

    def __init__(self, orchestrator: MultiAIOrchestrator) -> None:
        self.orchestrator = orchestrator
        self.steps: list[WorkflowStep] = []

    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)

    def remove_step(self, name: str) -> None:
        self.steps = [step for step in self.steps if step.name != name]

    def list_steps(self) -> list[str]:
        return [step.name for step in self.steps]

    def run(self, task: str, context: dict[str, Any] | None = None) -> WorkflowResult:
        if context is None:
            context = {}

        safe_context = dict(context)
        results: list[AgentResult] = []
        errors: list[str] = []
        previous_output: str | None = None
        final_output: str | None = None

        if not self.steps:
            return WorkflowResult(
                success=True,
                step_results=(),
                final_output=None,
                errors=(),
            )

        for step in self.steps:
            agents = self.orchestrator.get_agents_by_role(step.role)
            if not agents:
                error_message = f"Role uygun ajan bulunamadı: {step.role}"
                errors.append(error_message)
                return WorkflowResult(
                    success=False,
                    step_results=tuple(results),
                    final_output=final_output,
                    errors=tuple(errors),
                )

            agent = agents[0]
            template = step.task_template
            rendered_task = template.format(
                task=task,
                previous_output=previous_output or "",
            )

            step_context = dict(safe_context)
            if previous_output is not None:
                step_context["previous_output"] = previous_output

            agent_result = agent.run(rendered_task, context=step_context)
            results.append(agent_result)

            if agent_result.success:
                previous_output = agent_result.output
                final_output = agent_result.output
            else:
                errors.append(agent_result.error or "Bilinmeyen hata")
                if step.required:
                    return WorkflowResult(
                        success=False,
                        step_results=tuple(results),
                        final_output=final_output,
                        errors=tuple(errors),
                    )

        return WorkflowResult(
            success=all(result.success for result in results),
            step_results=tuple(results),
            final_output=final_output,
            errors=tuple(errors),
        )
