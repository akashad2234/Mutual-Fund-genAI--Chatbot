import json
from pathlib import Path

from src.phase1.main import run_phase1
from src.phase1.parse import parse_fund_page_html


def test_parse_fund_page_html_extracts_key_fields():
    html = """
    <html>
      <head>
        <title>Sample Fund Direct Growth - NAV, Mutual Fund Performance &amp; Portfolio</title>
      </head>
      <body>
        <div>
          <span>Min. for SIP</span>
          <span>₹100</span>
        </div>
        <div>
          <span>Expense ratio</span>
          <span>0.86%</span>
        </div>
        <h3>Return calculator</h3>
        <p>Example return calculator content.</p>
        <h3>Minimum investments</h3>
        <p>Min. for 1st investment ₹1,000. Min. for 2nd investment ₹1,000.</p>
        <h3>Exit load, stamp duty and tax</h3>
        <p>Exit load of 0.5%, if redeemed within 30 days. Stamp duty on investment: 0.005%.</p>
      </body>
    </html>
    """

    data = parse_fund_page_html(html, url="https://groww.in/test-fund", slug="test-fund")

    assert data.url == "https://groww.in/test-fund"
    assert data.slug == "test-fund"
    assert "Sample Fund Direct Growth" in (data.name or "")

    attrs = data.attributes
    assert attrs.expense_ratio == "0.86%"
    assert attrs.minimum_sip == "₹100"
    assert "0.5%" in (attrs.exit_load_summary or "")

    sections = data.sections
    assert sections["return_calculator"] is not None
    assert "Example return calculator content" in sections["return_calculator"]
    assert sections["minimum_investments"] is not None
    assert "Min. for 1st investment" in sections["minimum_investments"]
    assert sections["exit_load_stamp_duty_tax"] is not None


def test_run_phase1_creates_output_file(tmp_path, monkeypatch):
    """
    Integration-style test that runs the full Phase 1 pipeline against
    live Groww pages and verifies that:

    - At least one fund record is returned.
    - The JSON output file is created and contains valid JSON.
    """
    from src.phase1 import config as phase1_config

    # Redirect output paths to a temporary directory for the test.
    temp_data_dir = tmp_path / "data"
    temp_structured_dir = temp_data_dir / "structured"
    temp_structured_dir.mkdir(parents=True, exist_ok=True)
    temp_output_json = temp_structured_dir / "funds_phase1.json"

    monkeypatch.setattr(phase1_config, "DATA_DIR", str(temp_data_dir))
    monkeypatch.setattr(phase1_config, "STRUCTURED_DIR", str(temp_structured_dir))
    monkeypatch.setattr(phase1_config, "OUTPUT_JSON", str(temp_output_json))

    results = run_phase1()

    # Ensure we got some data back.
    assert isinstance(results, list)
    assert len(results) > 0

    # Ensure the JSON file was written and can be loaded.
    assert temp_output_json.exists()
    loaded = json.loads(temp_output_json.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    assert len(loaded) == len(results)

