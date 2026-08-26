import pytest
import redcell_core.config as config
from cryptography.fernet import Fernet
from pydantic import ValidationError
from redcell_core.config import Settings


def test_dev_generates_and_persists_secrets(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_DEV_SECRETS_DIR", tmp_path)
    s1 = Settings(env="dev", secret_key="", jwt_secret="", admin_password="")
    Fernet(s1.secret_key.encode())
    assert s1.jwt_secret
    assert s1.admin_password == "admin"
    assert s1.secure_cookies is False

    s2 = Settings(env="dev", secret_key="", jwt_secret="", admin_password="")
    assert s2.secret_key == s1.secret_key
    assert s2.jwt_secret == s1.jwt_secret


def test_non_dev_rejects_missing_secrets():
    with pytest.raises(ValidationError) as exc:
        Settings(env="production", secret_key="", jwt_secret="", admin_password="")
    msg = str(exc.value)
    assert "REDCELL_SECRET_KEY" in msg
    assert "REDCELL_JWT_SECRET" in msg
    assert "REDCELL_ADMIN_PASSWORD" in msg


def test_non_dev_rejects_default_admin_password():
    with pytest.raises(ValidationError) as exc:
        Settings(env="production", secret_key="k", jwt_secret="j", admin_password="admin")
    assert "REDCELL_ADMIN_PASSWORD" in str(exc.value)


def test_non_dev_rejects_whitespace_secrets():
    with pytest.raises(ValidationError) as exc:
        Settings(env="production", secret_key="   ", jwt_secret="\t", admin_password="  admin  ")
    msg = str(exc.value)
    assert "REDCELL_SECRET_KEY" in msg
    assert "REDCELL_JWT_SECRET" in msg
    assert "REDCELL_ADMIN_PASSWORD" in msg


def test_non_dev_accepts_real_secrets():
    s = Settings(env="production", jwt_secret="a-real-jwt-secret",
                 secret_key="a-real-fernet-key", admin_password="a-strong-password")
    assert s.secure_cookies is True


def test_secret_files_are_read(tmp_path):
    sk = tmp_path / "secret_key"
    jw = tmp_path / "jwt_secret"
    pw = tmp_path / "admin_password"
    sk.write_text("filed-fernet-key\n")
    jw.write_text("filed-jwt-secret\n")
    pw.write_text("filed-admin-password\n")
    s = Settings(env="production", secret_key="", jwt_secret="", admin_password="",
                 secret_key_file=str(sk), jwt_secret_file=str(jw), admin_password_file=str(pw))
    assert s.secret_key == "filed-fernet-key"
    assert s.jwt_secret == "filed-jwt-secret"
    assert s.admin_password == "filed-admin-password"


def test_explicit_env_beats_file(tmp_path):
    sk = tmp_path / "secret_key"
    sk.write_text("from-file")
    s = Settings(env="production", secret_key="from-env", jwt_secret="x", admin_password="y",
                 secret_key_file=str(sk))
    assert s.secret_key == "from-env"


def test_cookie_secure_override():
    s = Settings(env="production", jwt_secret="x", secret_key="y", admin_password="z",
                 cookie_secure=False)
    assert s.secure_cookies is False
