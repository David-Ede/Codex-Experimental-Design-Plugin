from __future__ import annotations

from doe_toolchain import LAUNCH_TOOL_NAMES
from doe_toolchain.server import registered_launch_tools


def test_launch_tool_registry_matches_contract() -> None:
    assert registered_launch_tools() == list(LAUNCH_TOOL_NAMES)
