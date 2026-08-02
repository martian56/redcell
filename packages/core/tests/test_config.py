from redcell_core.config import Settings, settings


def test_defaults_and_origins():
    assert settings.run_mode in ("sim", "live")
    # Assert the pure class default so the check is independent of the .env and of
    # the test suite's isolation overrides (conftest points buckets at test-*).
    assert Settings.model_fields["bucket_uploads"].default == "uploads"
    # origins splits a comma-separated string into a trimmed list.
    assert Settings(cors_origins="http://a, http://b").origins == ["http://a", "http://b"]
