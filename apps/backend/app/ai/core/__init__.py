__all__ = [
    "VertexCore",
    "IntentDetector",
    "Planner",
    "InputGuardrails",
    "OutputGuardrails",
    "PipelineLogger",
]


def __getattr__(name: str):
    if name == "VertexCore":
        from app.ai.core.vertex import VertexCore
        return VertexCore
    if name == "IntentDetector":
        from app.ai.core.intent import IntentDetector
        return IntentDetector
    if name == "Planner":
        from app.ai.core.planner import Planner
        return Planner
    if name == "InputGuardrails":
        from app.ai.core.guardrails import InputGuardrails
        return InputGuardrails
    if name == "OutputGuardrails":
        from app.ai.core.guardrails import OutputGuardrails
        return OutputGuardrails
    if name == "PipelineLogger":
        from app.ai.core.logging import PipelineLogger
        return PipelineLogger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

