from redcell_core.schemas import AgentEdge, Session


def test_camel_aliases():
    s = Session(id="s1", name="n", client="c", created_at="t")
    dumped = s.model_dump(by_alias=True)
    assert "createdAt" in dumped and "severityCounts" in dumped


def test_edge_from_alias():
    e = AgentEdge(**{"from": "a", "to": "b"})
    assert e.from_ == "a"
    assert e.model_dump(by_alias=True)["from"] == "a"
