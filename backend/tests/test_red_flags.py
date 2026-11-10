import pytest
from app.core.constants import TriageDisposition
from app.safety.red_flags import PreLLMRedFlagEngine


def test_cardiac_red_flag():
    result = PreLLMRedFlagEngine.evaluate("I have crushing chest pain radiating to my left arm")
    assert result.is_emergency is True
    assert result.matched_category == "cardiac"
    assert result.disposition == TriageDisposition.CALL_AMBULANCE_NOW


def test_stroke_red_flag():
    result = PreLLMRedFlagEngine.evaluate("My mother has sudden facial drooping and slurred speech")
    assert result.is_emergency is True
    assert result.matched_category == "stroke"
    assert result.disposition == TriageDisposition.CALL_AMBULANCE_NOW


def test_respiratory_red_flag():
    result = PreLLMRedFlagEngine.evaluate("I cannot breathe and I am gasping for air")
    assert result.is_emergency is True
    assert result.matched_category == "respiratory"
    assert result.disposition == TriageDisposition.CALL_AMBULANCE_NOW


def test_anaphylaxis_red_flag():
    result = PreLLMRedFlagEngine.evaluate("My throat is closing and my tongue is swelling")
    assert result.is_emergency is True
    assert result.matched_category == "anaphylaxis"
    assert result.disposition == TriageDisposition.CALL_AMBULANCE_NOW


def test_severe_bleeding_red_flag():
    result = PreLLMRedFlagEngine.evaluate("I am coughing up large amounts of blood")
    assert result.is_emergency is True
    assert result.matched_category == "severe_bleeding"
    assert result.disposition == TriageDisposition.CALL_AMBULANCE_NOW


def test_severe_abdominal_pain_red_flag():
    result = PreLLMRedFlagEngine.evaluate("Severe lower abdominal pain, pain is 8 out of 10")
    assert result.is_emergency is True
    assert result.matched_category == "severe_abdominal"
    assert result.disposition == TriageDisposition.EMERGENCY_ROOM_IMMEDIATELY


def test_non_emergency_symptoms():
    result = PreLLMRedFlagEngine.evaluate("I have had a mild dry cough and runny nose for 2 days")
    assert result.is_emergency is False
    assert result.matched_category is None
    assert result.disposition is None


def test_empty_message():
    result = PreLLMRedFlagEngine.evaluate("   ")
    assert result.is_emergency is False
