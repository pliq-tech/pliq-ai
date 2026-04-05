"""Agent orchestration utilities for parallel execution and result merging."""

import asyncio
import logging
import time
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentStepResult:
    """Result of a single agent execution step."""

    agent_name: str
    success: bool
    result: dict | None = None
    error: str | None = None
    latency_ms: float = 0.0


@dataclass
class OrchestratedResult:
    """Merged result from multiple agent steps."""

    results: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    total_latency_ms: float = 0.0
    step_count: int = 0
    success_count: int = 0
    failure_count: int = 0


async def run_with_timeout(
    coro: Coroutine,
    timeout_seconds: float,
    agent_name: str,
) -> AgentStepResult:
    """Run a coroutine with timeout and error handling.

    Args:
        coro: The async coroutine to execute.
        timeout_seconds: Maximum time in seconds before cancellation.
        agent_name: Identifier for logging and result tracking.

    Returns:
        AgentStepResult with success/failure status and timing.
    """
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(coro, timeout=timeout_seconds)
        latency = (time.monotonic() - start) * 1000
        logger.info(
            "Agent '%s' completed in %.1fms",
            agent_name,
            latency,
        )
        return AgentStepResult(
            agent_name=agent_name,
            success=True,
            result=result,
            latency_ms=latency,
        )
    except TimeoutError:
        latency = (time.monotonic() - start) * 1000
        logger.warning(
            "Agent '%s' timed out after %.1fms (limit: %.0fs)",
            agent_name,
            latency,
            timeout_seconds,
        )
        return AgentStepResult(
            agent_name=agent_name,
            success=False,
            error=f"Timeout after {timeout_seconds}s",
            latency_ms=latency,
        )
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        logger.error(
            "Agent '%s' failed after %.1fms: %s",
            agent_name,
            latency,
            exc,
            exc_info=True,
        )
        return AgentStepResult(
            agent_name=agent_name,
            success=False,
            error=str(exc),
            latency_ms=latency,
        )


async def run_parallel_agents(
    steps: list[tuple[str, Coroutine]],
    timeout: float = 30.0,
) -> list[AgentStepResult]:
    """Run multiple agent steps in parallel with per-step timeouts.

    Each step gets its own timeout. Steps that fail or time out do not
    affect other steps (graceful degradation).

    Args:
        steps: List of (agent_name, coroutine) tuples.
        timeout: Maximum seconds per individual step.

    Returns:
        List of AgentStepResult in the same order as input steps.
    """
    if not steps:
        return []

    tasks = [
        run_with_timeout(coro, timeout, name) for name, coro in steps
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)


async def run_sequential_agents(
    steps: list[tuple[str, Coroutine]],
    timeout: float = 30.0,
    stop_on_failure: bool = False,
) -> list[AgentStepResult]:
    """Run agent steps sequentially with optional early termination.

    Args:
        steps: List of (agent_name, coroutine) tuples.
        timeout: Maximum seconds per individual step.
        stop_on_failure: If True, stop executing remaining steps
                         after the first failure.

    Returns:
        List of AgentStepResult for all executed steps.
    """
    results: list[AgentStepResult] = []

    for name, coro in steps:
        step_result = await run_with_timeout(coro, timeout, name)
        results.append(step_result)

        if stop_on_failure and not step_result.success:
            logger.warning(
                "Sequential pipeline stopped at '%s' due to failure",
                name,
            )
            break

    return results


def merge_results(step_results: list[AgentStepResult]) -> OrchestratedResult:
    """Merge results from multiple agent steps into a unified output.

    Successful results are collected by agent name. Failed steps
    generate warnings with the error details.

    Args:
        step_results: List of AgentStepResult from parallel or sequential runs.

    Returns:
        OrchestratedResult with merged data and failure warnings.
    """
    merged = OrchestratedResult()
    merged.step_count = len(step_results)

    for step in step_results:
        merged.total_latency_ms = max(merged.total_latency_ms, step.latency_ms)

        if step.success:
            merged.success_count += 1
            merged.results[step.agent_name] = step.result
        else:
            merged.failure_count += 1
            warning = f"{step.agent_name}: {step.error}"
            merged.warnings.append(warning)
            logger.warning("Agent step failed: %s", warning)

    return merged
