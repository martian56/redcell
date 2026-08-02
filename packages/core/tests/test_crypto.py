from redcell_core.crypto import decrypt, encrypt


def test_round_trip():
    ct = encrypt("hunter2")
    assert ct != "hunter2"
    assert decrypt(ct) == "hunter2"


def test_empty_safe():
    assert encrypt("") == ""
    assert decrypt("") == ""
    assert encrypt(None) == ""
    assert decrypt(None) == ""
