from redcell_core.engine.kinds import KINDS, OrchestratorContext, get_kind


def test_registry_has_core_kinds():
    assert set(KINDS) >= {"general", "network", "code"}


def test_get_kind_falls_back_to_general():
    assert get_kind(None).id == "general"
    assert get_kind("").id == "general"
    assert get_kind("does-not-exist").id == "general"
    assert get_kind("CODE").id == "code"


def test_general_is_full_capability():
    g = get_kind("general")
    assert g.uses_browser and g.seeds_hosts and g.exploits and not g.mounts_source
    assert "authorized security engagement" in g.orchestrator_system(
        OrchestratorContext(goal="G", scope=[], targets=[]))


def test_network_and_code_flags():
    net = get_kind("network")
    assert net.uses_browser and net.seeds_hosts and net.exploits and not net.mounts_source
    code = get_kind("code")
    assert code.mounts_source and not code.uses_browser and not code.seeds_hosts and not code.exploits


def test_prompts_reflect_kind():
    net = get_kind("network").orchestrator_system(
        OrchestratorContext(goal="G", scope=["*.x"], targets=["x"]))
    assert "authorized red-team engagement" in net
    code = get_kind("code").orchestrator_system(
        OrchestratorContext(goal="Review", scope=[], targets=[], source="/src"))
    assert "source-code security review" in code
