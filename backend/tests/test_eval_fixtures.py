import json
from pathlib import Path


def test_eval_fixture_file_is_present_and_valid_json() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "report_eval_cases.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 2
    for case in data:
        assert "case_id" in case
        assert "utterances" in case
        assert "expected" in case
