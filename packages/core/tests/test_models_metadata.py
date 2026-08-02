from redcell_core.models import Base


def test_all_tables_registered():
    tables = set(Base.metadata.tables)
    expected = {"users", "providers", "app_settings", "sessions", "runs",
                "agents", "agent_edges", "findings", "shells", "listeners",
                "proxy_entries", "hosts", "loot", "chat_messages", "servers",
                "proxies", "files", "reports"}
    assert expected <= tables
