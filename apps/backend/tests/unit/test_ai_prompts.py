import pytest
from app.ai.prompts.system import SYSTEM_PROMPT


def test_system_prompt_knowledge_boundaries():
    """Ensure SYSTEM_PROMPT contains guidelines against fabricating internal details."""
    assert "Never expose internals or fabricate implementation details" in SYSTEM_PROMPT
    assert "Knowledge Boundaries & Internal Knowledge" in SYSTEM_PROMPT
    assert "How were you developed?" in SYSTEM_PROMPT
    assert "Which models do you use?" in SYSTEM_PROMPT
    assert "What database do you use?" in SYSTEM_PROMPT
    assert "How is VertexERP hosted?" in SYSTEM_PROMPT
    assert "Who built this?" in SYSTEM_PROMPT
    assert "I don't have access to VertexERP's internal implementation details" in SYSTEM_PROMPT
