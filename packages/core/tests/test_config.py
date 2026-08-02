from redcell_core.config import Settings, settings


def test_defaults_and_origins():
    assert settings.run_mode in ("sim", "live")
    # check the class default, not the live instance, so .env and conftest's
    # test-* bucket overrides can't sway it.
    assert Settings.model_fields["bucket_uploads"].default == "uploads"
    # origins splits a comma-separated string into a trimmed list.
    assert Settings(cors_origins="http://a, http://b").origins == ["http://a", "http://b"]
