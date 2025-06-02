# test_report.py

import textwrap
from pathlib import Path

import pytest

from main import report_func


@pytest.fixture(scope="session")
def correct_data():
    return textwrap.dedent("""\
    id,email,name,department,hours_worked,hourly_rate
    1,alice@example.com,Alice Johnson,Marketing,160,50
    2,bob@example.com,Bob Smith,Design,150,40
    3,carol@example.com,Carol Williams,Design,170,60
    """)


def test_payout_report(monkeypatch, capsys, correct_data):
    fake_path = "data.csv"

    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(Path, "read_text", lambda self, encoding="utf-8": correct_data)

    report_func(fake_path, report="TestReport", report_type="payout")
    captured = capsys.readouterr()
    output_lines = [line.strip() for line in captured.out.strip().splitlines()]

    expected = [
        "['1', 'alice@example.com', 'Alice Johnson', 'Marketing', '160', '50', '8000']",
        "['2', 'bob@example.com', 'Bob Smith', 'Design', '150', '40', '6000']",
        "['3', 'carol@example.com', 'Carol Williams', 'Design', '170', '60', '10200']",
    ]
    assert output_lines == expected
