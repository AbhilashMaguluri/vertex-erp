import pytest

from app.ai.core.goal import GoalBuilder
from app.ai.core.intent import RuleBasedIntentDetector
from app.ai.core.ownership import DataOwnershipResolver
from app.ai.core.planner import Planner
from app.ai.models.context import PageContext, UserContext, VertexContext
from app.ai.models.goal import GoalTarget, GoalType
from app.ai.models.intent import IntentCategory
from app.ai.models.plan import PlanAction
from app.ai.tools.registry_setup import get_registry
from app.ai.tools.ui_tool import UITool, ToolExecutionContext


@pytest.mark.asyncio
async def test_theme_change_goal_and_plan_resolution():
    goal_builder = GoalBuilder()
    intent_detector = RuleBasedIntentDetector()
    ownership_resolver = DataOwnershipResolver()
    planner = Planner()
    registry = get_registry()

    context = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "light", "resolvedTheme": "light"}),
        mode="student",
    )

    goal = await goal_builder.build("switch to dark mode", context)
    assert goal.target == GoalTarget.APPLICATION_STATE
    assert goal.parameters.get("action") == "setTheme"
    assert goal.parameters.get("mode") == "dark"

    intent = await intent_detector.detect("switch to dark mode", goal, context)
    assert intent.category == IntentCategory.THEME_CHANGE

    ownership = ownership_resolver.resolve(goal, context)
    plan = await planner.plan(goal, intent, ownership, context, registry)
    assert plan.action == PlanAction.EXECUTE_TOOL
    assert plan.tool_name == "ui"
    assert plan.tool_action == "setTheme"
    assert plan.tool_params == {"mode": "dark"}


@pytest.mark.asyncio
async def test_theme_query_goal_and_plan_resolution():
    goal_builder = GoalBuilder()
    intent_detector = RuleBasedIntentDetector()
    ownership_resolver = DataOwnershipResolver()
    planner = Planner()
    registry = get_registry()

    context = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "dark", "resolvedTheme": "dark"}),
        mode="student",
    )

    goal = await goal_builder.build("what is my current theme?", context)
    assert goal.target == GoalTarget.APPLICATION_STATE
    assert goal.parameters.get("action") == "getCurrentTheme"

    intent = await intent_detector.detect("what is my current theme?", goal, context)
    assert intent.category == IntentCategory.THEME_CHANGE

    ownership = ownership_resolver.resolve(goal, context)
    plan = await planner.plan(goal, intent, ownership, context, registry)
    assert plan.action == PlanAction.EXECUTE_TOOL
    assert plan.tool_name == "ui"
    assert plan.tool_action == "getCurrentTheme"


@pytest.mark.asyncio
async def test_ui_tool_set_theme_verifies_live_state():
    ui_tool = UITool()

    # Case 1: Requested theme is already active in live UI state
    context_same = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "dark", "resolvedTheme": "dark"}),
        mode="student",
    )
    exec_ctx_same = ToolExecutionContext(vertex=context_same, request_id="req1")

    res_same = await ui_tool.execute("setTheme", {"mode": "dark"}, exec_ctx_same)
    assert res_same.success is True
    assert res_same.data.get("already_active") is True
    assert res_same.ui_action is None

    # Case 2: Requested theme is different from live UI state
    context_diff = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "light", "resolvedTheme": "light"}),
        mode="student",
    )
    exec_ctx_diff = ToolExecutionContext(vertex=context_diff, request_id="req2")

    res_diff = await ui_tool.execute("setTheme", {"mode": "dark"}, exec_ctx_diff)
    assert res_diff.success is True
    assert res_diff.data.get("already_active") is not True
    assert res_diff.ui_action == {"type": "setTheme", "mode": "dark"}


@pytest.mark.asyncio
async def test_ui_tool_get_current_theme_reads_live_state():
    ui_tool = UITool()
    context = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "system", "resolvedTheme": "dark"}),
        mode="student",
    )
    exec_ctx = ToolExecutionContext(vertex=context, request_id="req3")

    result = await ui_tool.execute("getCurrentTheme", {}, exec_ctx)
    assert result.success is True
    assert result.data == {"theme": "system", "resolved": "dark"}


@pytest.mark.asyncio
async def test_generic_theme_phrases_and_toggle_resolution():
    goal_builder = GoalBuilder()
    intent_detector = RuleBasedIntentDetector()
    ownership_resolver = DataOwnershipResolver()
    planner = Planner()
    registry = get_registry()

    phrases = [
        "switch theme",
        "change theme",
        "toggle theme",
        "switch appearance",
        "change appearance",
        "toggle appearance",
    ]

    context = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "dark", "resolvedTheme": "dark"}),
        mode="student",
    )

    for phrase in phrases:
        goal = await goal_builder.build(phrase, context)
        assert goal.target == GoalTarget.APPLICATION_STATE
        assert goal.parameters.get("action") == "toggleTheme"

        intent = await intent_detector.detect(phrase, goal, context)
        assert intent.category == IntentCategory.THEME_CHANGE

        ownership = ownership_resolver.resolve(goal, context)
        plan = await planner.plan(goal, intent, ownership, context, registry)
        assert plan.action == PlanAction.EXECUTE_TOOL
        assert plan.tool_name == "ui"
        assert plan.tool_action == "toggleTheme"


@pytest.mark.asyncio
async def test_ui_tool_toggle_theme_execution():
    ui_tool = UITool()

    # From dark to light
    ctx_dark = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "dark", "resolvedTheme": "dark"}),
        mode="student",
    )
    res_dark = await ui_tool.execute("toggleTheme", {}, ToolExecutionContext(vertex=ctx_dark, request_id="t1"))
    assert res_dark.success is True
    assert res_dark.data == {"mode": "light", "previous": "dark"}
    assert res_dark.ui_action == {"type": "setTheme", "mode": "light"}

    # From light to dark
    ctx_light = VertexContext(
        user=UserContext(is_authenticated=True),
        page=PageContext(page="dashboard", state={"theme": "light", "resolvedTheme": "light"}),
        mode="student",
    )
    res_light = await ui_tool.execute("toggleTheme", {}, ToolExecutionContext(vertex=ctx_light, request_id="t2"))
    assert res_light.success is True
    assert res_light.data == {"mode": "dark", "previous": "light"}
    assert res_light.ui_action == {"type": "setTheme", "mode": "dark"}
