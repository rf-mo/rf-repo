from app.rules import extract_followups, infer_intention_bucket, infer_outcomes, infer_play, infer_tags


def test_tag_detection():
    note = "Ran workshop and drafted SOW with talk track objection checklist"
    tags = infer_tags(note)
    assert "workshop" in tags
    assert "SOW" in tags
    assert "talk track" in tags


def test_play_and_bucket_classification():
    note = "AI readiness infra foundation checklist for customer"
    assert infer_play(note) == "AI Readiness"
    assert infer_intention_bucket(note, "meeting") == "B"


def test_outcomes_and_followups_detection():
    note = "Workshop scheduled, follow up by Friday and send deck"
    outcomes = infer_outcomes(note)
    assert "workshop proposed" in outcomes
    assert "workshop scheduled" in outcomes
    assert "asset created" in outcomes
    followups = extract_followups(note)
    assert len(followups) == 1
