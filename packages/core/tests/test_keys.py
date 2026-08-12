"""Unit tests for SSH private-key normalization, which reflows single-line
pasted keys back into valid PEM and leaves everything else untouched."""

from redcell_core.keys import normalize_private_key


def test_none_and_empty_pass_through():
    assert normalize_private_key(None) is None
    assert normalize_private_key("") == ""


def test_non_key_text_is_left_alone():
    assert normalize_private_key("hunter2") == "hunter2"
    assert normalize_private_key("  a passphrase  ") == "  a passphrase  "


def test_text_mentioning_private_key_without_markers_is_untouched():
    # Has the phrase but no BEGIN/END block: hand it back so the parser reports
    # the real error rather than us guessing.
    weird = "this PRIVATE KEY looks broken"
    assert normalize_private_key(weird) == weird


def test_multiline_pem_is_preserved_with_trailing_newline():
    pem = ("-----BEGIN OPENSSH PRIVATE KEY-----\n"
           "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAAB\n"
           "AAAAMwAAAAtzc2gtZWQyNTUxOQAAACDrealkeymaterialheregoes\n"
           "-----END OPENSSH PRIVATE KEY-----")
    out = normalize_private_key(pem)
    assert out.startswith("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    assert out.endswith("-----END OPENSSH PRIVATE KEY-----\n")
    assert "b3BlbnNzaC1rZXktdjEA" in out


def test_singleline_pem_is_reflowed_to_64_columns():
    body = "A" * 130  # a base64-ish blob with the line breaks stripped out
    blob = f"-----BEGIN RSA PRIVATE KEY----- {body} -----END RSA PRIVATE KEY-----"
    out = normalize_private_key(blob)
    lines = out.splitlines()
    assert lines[0] == "-----BEGIN RSA PRIVATE KEY-----"
    assert lines[-1] == "-----END RSA PRIVATE KEY-----"
    middle = lines[1:-1]
    assert all(len(line) <= 64 for line in middle)
    assert "".join(middle) == body  # reflow preserves the payload exactly
    assert out.endswith("\n")
