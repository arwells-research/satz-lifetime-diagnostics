from pathlib import Path
import json

def test_frozen_law_exists_and_is_json():
    p = Path("data/processed/frozen_law_phase1.json")
    assert p.exists(), "Missing frozen law artifact"
    data = json.loads(p.read_text())
    assert isinstance(data, dict), "Frozen law JSON should be an object"
    # Keep this permissive: we only enforce presence of keys, not values
    # (values are frozen and validated by experiment scripts).
    assert any(k.lower().startswith("alpha") or k.lower() == "alpha" for k in data.keys())
    assert any(k.lower().startswith("delta") or k.lower() == "delta" for k in data.keys())

def test_processed_stack_exists():
    p = Path("data/processed/beta_vertical_stacks.csv")
    assert p.exists(), "Missing processed stack CSV"