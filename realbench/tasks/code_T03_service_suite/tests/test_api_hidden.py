"""Hidden tests: api module — pipeline composition."""
from api import process_line
from store import EventStore


def test_ok_flow():
    store = EventStore(10)
    r = process_line("TS=1 TYPE=click VAL=1.0", store, {})
    assert r == {"status": "ok"}
    assert store.count() == 1


def test_parse_error_flow():
    store = EventStore(10)
    r = process_line("TS=1 TYPE=click", store, {})
    assert r["status"] == "error"
    assert "error" in r and r["error"]


def test_validation_reject_flow():
    store = EventStore(10)
    rules = {"allowed_types": ["view"]}
    r = process_line("TS=1 TYPE=click VAL=1.0", store, rules)
    assert r == {"status": "rejected"}
    assert store.count() == 0


def test_store_reject_flow():
    store = EventStore(1)
    assert process_line("TS=10 TYPE=x VAL=1", store, {})["status"] == "ok"
    r = process_line("TS=5 TYPE=x VAL=1", store, {})
    assert r == {"status": "rejected"}  # older event, store refuses


def test_full_pipeline_many_lines():
    store = EventStore(100)
    ok = rej = err = 0
    for i in range(50):
        r = process_line(f"TS={i} TYPE=evt VAL={i}", store, {"min_ts": 10})
        if r["status"] == "ok":
            ok += 1
        elif r["status"] == "rejected":
            rej += 1
        else:
            err += 1
    assert ok == 40      # ts 10..49 accepted
    assert rej == 10     # ts 0..9 rejected by min_ts
    assert err == 0
    assert store.count() == 40
