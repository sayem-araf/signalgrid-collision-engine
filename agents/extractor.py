import json
import os
import re
import urllib.request
from dataclasses import fields
from typing import Optional, Tuple

from schemas import ExtractedEvent

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
FIELDS = [f.name for f in fields(ExtractedEvent)]
INT_FIELDS = {"need_week", "delay_weeks", "delay_best_weeks", "delay_worst_weeks", "policy_delay_weeks"}

SYSTEM = (
    "You structure infrastructure and supply-chain signals for a protection relay planner. "
    "Return ONLY a JSON object with these keys: project (str), mw (number), need_week (int, weeks from today), "
    "delay_weeks (int, likely supplier delay), delay_best_weeks (int), delay_worst_weeks (int), "
    "policy_delay_weeks (int, 0 if no trade/policy signal), critical_part (str), market_tightness (str), "
    "source (str), supply_concentration ('Single region' | 'Few regions' | 'Diversified'). "
    "Use only what the text states; if a value is missing, use 0 or 'Unknown'. Do not invent figures."
)


class SignalExtractionAgent:
    """The only language-model step. It structures text; it does not calculate or decide.
    Returns (event, status) where status says whether the result is live or cached."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or DEFAULT_MODEL

    def extract(self, raw_text: str, fixture_path: Optional[str] = None) -> Tuple[ExtractedEvent, str]:
        if not self.api_key:
            return self._load_fallback(fixture_path, "Cached extraction (no API key)")
        payload = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": 0.0,
            "system": SYSTEM,
            "messages": [{"role": "user", "content": raw_text}],
        }
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "x-api-key": self.api_key,
                         "anthropic-version": "2023-06-01"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            text = result["content"][0]["text"].strip()
            return self._parse(text), f"Live extraction ({self.model})"
        except Exception as e:  # network, model, or parse failure -> visible fallback
            return self._load_fallback(fixture_path, f"Cached extraction (live call failed: {type(e).__name__})")

    @staticmethod
    def _parse(text: str) -> ExtractedEvent:
        m = re.search(r"\{.*\}", text, re.S)  # tolerate ```json fences or prose
        if not m:
            raise ValueError("No JSON object in response")
        data = json.loads(m.group(0))
        clean = {k: v for k, v in data.items() if k in FIELDS}
        for k in INT_FIELDS:
            if k in clean and clean[k] is not None:
                clean[k] = int(round(float(clean[k])))
        if "mw" in clean:
            clean["mw"] = max(0.0, float(clean["mw"]))
        if "project" not in clean:
            raise ValueError("Missing project")
        clean.setdefault("mw", 0.0)
        return ExtractedEvent(**clean)

    @staticmethod
    def _load_fallback(fixture_path: Optional[str], status: str) -> Tuple[ExtractedEvent, str]:
        target = fixture_path or os.path.join(os.path.dirname(__file__), "..", "fixtures", "scenario_a.json")
        with open(target, "r") as f:
            data = json.load(f)
        return ExtractedEvent(**{k: v for k, v in data.items() if k in FIELDS}), status
