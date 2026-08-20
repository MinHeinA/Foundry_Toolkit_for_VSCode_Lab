from careers_job_mcp.sanitize import sanitize_html


def test_sanitizer_removes_executable_markup_and_controls() -> None:
    raw = (
        '<p onclick="steal()">Hello&nbsp;world</p>'
        "<script>alert(document.cookie)</script>"
        "<style>body{display:none}</style>"
        "<svg><script>bad()</script></svg>"
        "<!-- secret --><p>Safe&#x20;text\u0000</p>"
    )
    result = sanitize_html(raw)

    assert result == "Hello world\nSafe text"
    assert "onclick" not in result
    assert "alert" not in result
    assert "<" not in result
    assert "\u0000" not in result


def test_sanitizer_handles_encoded_and_malformed_xss() -> None:
    raw = "&lt;script&gt;encodedBad()&lt;/script&gt;<p>Kept &amp; decoded"
    result = sanitize_html(raw)

    assert "encodedBad" not in result
    assert result == "Kept & decoded"


def test_sanitizer_normalizes_unicode_and_whitespace() -> None:
    assert sanitize_html("<p>ＡＢＣ   test</p><p>next\tline</p>") == "ABC test\nnext line"

