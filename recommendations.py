class RecommendationEngine:
    def __init__(self):
        pass

    def _immediate_action(self, category: str, stress: int, fatigue: int) -> dict:
        if category in ("Critical", "Significant") or stress >= 80 or fatigue >= 80:
            return {
                "urgency": "High",
                "action": "Take a 5–10 minute break now. Hydrate, step away from screens, and do a guided breathing cycle before continuing.",
            }
        if category in ("Moderate", "Fair"):
            return {
                "urgency": "Medium",
                "action": "Plan a short rest in the next 30 minutes. Reduce cognitive load and check posture and lighting.",
            }
        return {
            "urgency": "Low",
            "action": "Maintain current routine. Do a brief stretch and continue to monitor energy levels.",
        }

    def _breathing(self, category: str) -> dict:
        if category in ("Critical", "Significant", "Moderate"):
            return {
                "name": "Box Breathing (4-4-4-4)",
                "instructions": [
                    "Inhale through the nose for 4 seconds",
                    "Hold for 4 seconds",
                    "Exhale through the mouth for 4 seconds",
                    "Hold for 4 seconds and repeat for 1–2 minutes",
                ],
            }
        return {
            "name": "Coherent Breathing (5-5)",
            "instructions": [
                "Inhale gently for 5 seconds",
                "Exhale gently for 5 seconds",
                "Repeat 10–12 cycles",
            ],
        }

    def _personalized(self, data: dict) -> list:
        recs = []
        stress = data.get("stress_score", 0)
        fatigue = data.get("fatigue_score", 0)
        idx = data.get("wellness_index", 100)

        if stress >= 70:
            recs.append("Reduce multitasking; focus on one task for the next 20 minutes.")
            recs.append("Use a short mindfulness check-in (body scan, 1 minute).")
        if fatigue >= 70:
            recs.append("Hydrate and consider a light snack (protein + complex carbs).")
            recs.append("Stand up and do 1–2 minutes of light movement or stretching.")
        if idx < 70:
            recs.append("Adjust environment: lower screen brightness, reduce noise, optimize seating.")
        if idx >= 80:
            recs.append("Maintain current habits; schedule a brief walk later today.")
        if stress < 40 and fatigue < 40:
            recs.append("Consider a focused deep-work block of 45–60 minutes.")

        if not recs:
            recs.append("Keep monitoring and aim for consistent sleep and nutrition routines.")
        return recs[:6]

    def generate_report(self, wellness_data: dict) -> dict:
        category = wellness_data.get("category", "Good")
        stress = int(wellness_data.get("stress_score", 0))
        fatigue = int(wellness_data.get("fatigue_score", 0))

        return {
            "immediate_action": self._immediate_action(category, stress, fatigue),
            "personalized_recommendations": self._personalized(wellness_data),
            "breathing_exercise": self._breathing(category),
        }

