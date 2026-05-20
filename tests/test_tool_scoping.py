from honeyagentbench.tools import (
    TOOL_KIND_FINAL_REPORT,
    TOOL_KIND_NETWORK,
    TOOL_KIND_REPORT_SUSPICION,
    TOOL_KIND_SSH,
    TOOL_KIND_WEB,
    tool_kinds_for_environment,
)


def test_ssh_environment_exposes_only_ssh_and_report_tools():
    assert tool_kinds_for_environment("ssh_like") == (
        TOOL_KIND_SSH,
        TOOL_KIND_REPORT_SUSPICION,
        TOOL_KIND_FINAL_REPORT,
    )


def test_web_environment_exposes_only_web_and_report_tools():
    assert tool_kinds_for_environment("web") == (
        TOOL_KIND_WEB,
        TOOL_KIND_REPORT_SUSPICION,
        TOOL_KIND_FINAL_REPORT,
    )


def test_multinode_environment_exposes_only_network_and_report_tools():
    assert tool_kinds_for_environment("multi_node") == (
        TOOL_KIND_NETWORK,
        TOOL_KIND_REPORT_SUSPICION,
        TOOL_KIND_FINAL_REPORT,
    )


def test_unknown_environment_keeps_all_tools_for_compatibility():
    assert tool_kinds_for_environment(None) == (
        TOOL_KIND_SSH,
        TOOL_KIND_WEB,
        TOOL_KIND_NETWORK,
        TOOL_KIND_REPORT_SUSPICION,
        TOOL_KIND_FINAL_REPORT,
    )
