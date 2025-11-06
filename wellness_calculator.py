import json
from datetime import datetime
from pathlib import Path


class WellnessCalculator:
    def __init__(self, history_path: str = "wellness_history.json"):
        self.history_file = Path(history_path)
        self.history = []

    def load_history(self) -> None:
        try:
            if self.history_file.exists():
                self.history = json.loads(self.history_file.read_text(encoding="utf-8"))
            else:
                self.history = []
        except Exception:
            self.history = []

    def _category_from_index(self, idx: float) -> str:
        if idx >= 90:
            return "Excellent"
        if idx >= 80:
            return "Good"
        if idx >= 70:
            return "Fair"
        if idx >= 60:
            return "Moderate"
        if idx >= 50:
            return "Significant"
        return "Critical"

    def _indicator_from_index(self, idx: float) -> str:
        if idx >= 80:
            return "🟢"
        if idx >= 70:
            return "🟡"
        if idx >= 60:
            return "🟠"
        return "🔴"

    def _risk_from_scores(self, stress: int, fatigue: int) -> str:
        avg = 0.6 * stress + 0.4 * fatigue
        if avg >= 80:
            return "High"
        if avg >= 60:
            return "Moderate"
        return "Low"

    def _compute_wellness_index(self, stress: int, fatigue: int) -> float:
        stress = max(0, min(100, int(stress)))
        fatigue = max(0, min(100, int(fatigue)))
        burden = 0.6 * stress + 0.4 * fatigue
        index = 100.0 - burden
        return max(0.0, min(100.0, index))

    def _save(self) -> None:
        try:
            self.history_file.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def analyze_complete(self, stress_score: int, fatigue_score: int) -> dict:
        wellness_index = round(self._compute_wellness_index(stress_score, fatigue_score), 2)
        category = self._category_from_index(wellness_index)
        indicator = self._indicator_from_index(wellness_index)
        risk_level = self._risk_from_scores(stress_score, fatigue_score)

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stress_score": int(stress_score),
            "fatigue_score": int(fatigue_score),
            "wellness_index": float(wellness_index),
            "category": category,
        }

        self.history.append(record)
        # keep last 100 entries
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self._save()

        return {
            "indicator": indicator,
            "wellness_index": wellness_index,
            "category": category,
            "stress_score": int(stress_score),
            "fatigue_score": int(fatigue_score),
            "risk_level": risk_level,
        }

    def get_trend_analysis(self):
        if not self.history:
            return "Not enough data yet"
        last = self.history[-5:]
        avg = sum(x["wellness_index"] for x in last) / len(last)
        if len(last) >= 2:
            trend = "up" if last[-1]["wellness_index"] > last[0]["wellness_index"] else ("down" if last[-1]["wellness_index"] < last[0]["wellness_index"] else "flat")
        else:
            trend = "flat"
        return {
            "average_wellness": round(avg, 2),
            "trend": trend,
            "sessions_count": len(self.history),
        }

