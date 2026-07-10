from pathlib import Path

EXPECTED_PINS = {
    "anthropic": "0.116.0",
    "pymupdf": "1.28.0",
    "pdfplumber": "0.11.10",
    "python-dotenv": "1.2.2",
    "gspread": "6.2.1",
    "google-auth": "2.55.2",
    "google-auth-oauthlib": "1.4.0",
    "google-api-python-client": "2.198.0",
    "openpyxl": "3.1.5",
    "requests": "2.34.2",
    "streamlit": "1.59.1",
    "pandas": "2.3.3",
    "filelock": "3.29.7",
}


def _production_requirement_lines():
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    for raw_line in requirements.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            yield line


def test_production_dependencies_are_pinned_to_verified_python312_versions():
    lines = list(_production_requirement_lines())

    for package, version in EXPECTED_PINS.items():
        assert f"{package}=={version}" in lines

    assert all(">=" not in line and "<" not in line for line in lines)
