from redcell_core.engine.kinds import KINDS, OrchestratorContext, get_kind


def test_registry_has_core_kinds():
    assert set(KINDS) >= {"general", "network", "osint", "code"}


def test_osint_is_passive():
    o = get_kind("osint")
    assert o.uses_browser and o.seeds_hosts and not o.exploits and not o.mounts_source
    p = o.orchestrator_system(OrchestratorContext(goal="Profile", scope=["acme.com"], targets=[]))
    assert "OSINT engagement" in p
    assert "passive" in p.lower()


def test_get_kind_falls_back_to_general():
    assert get_kind(None).id == "general"
    assert get_kind("").id == "general"
    assert get_kind("does-not-exist").id == "general"
    assert get_kind("CODE").id == "code"


def test_mobile_is_a_static_kind_on_the_mobile_image():
    m = get_kind("mobile")
    assert m.id == "mobile" and m.available is True
    assert not m.uses_browser and not m.seeds_hosts and not m.exploits and not m.mounts_source
    assert m.image_setting == "mobile_docker_image"
    p = m.orchestrator_system(OrchestratorContext(goal="Review app", scope=[], targets=[],
                                                   files=["app.apk"]))
    assert "mobile application security review" in p
    assert "/root/assessment/: app.apk" in p


def test_default_kind_uses_the_kali_image_setting():
    assert get_kind("network").image_setting == "docker_image"
    assert get_kind("general").image_setting == "docker_image"


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


def test_offensive_prompts_carry_tradecraft():
    ctx = OrchestratorContext(goal="G", scope=["*.x"], targets=["x"])
    for kind in ("network", "general"):
        p = get_kind(kind).orchestrator_system(ctx)
        assert "not a scan pipeline" in p
        assert "probe by hand" in p
        assert "CHAIN" in p
    ex = get_kind("network").executor_system("web-exploit", "test auth")
    assert "test by hand" in ex


def test_prompts_reflect_kind():
    net = get_kind("network").orchestrator_system(
        OrchestratorContext(goal="G", scope=["*.x"], targets=["x"]))
    assert "authorized red-team engagement" in net
    code = get_kind("code").orchestrator_system(
        OrchestratorContext(goal="Review", scope=[], targets=[], source="/src"))
    assert "source-code security review" in code
