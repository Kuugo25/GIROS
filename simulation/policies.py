# policies.py
class ResinPolicy:
    def choose_activity(self, character):
        raise NotImplementedError

    def evaluate_upgrade(self, before_dps, after_dps, resin_cost):
        raise NotImplementedError


class MinMaxerPolicy(ResinPolicy):
    def choose_activity(self, character):
        # Prefers high-variance, high-reward activities like artifact farming
        return "artifact_farm"

    def evaluate_upgrade(self, before_dps, after_dps, resin_cost):
        gain = after_dps - before_dps
        return gain > 50


class PlannerPolicy(ResinPolicy):
    def choose_activity(self, character):
        # Prefers consistent gains like talent upgrades
        return "talent_farm"

    def evaluate_upgrade(self, before_dps, after_dps, resin_cost):
        gain = after_dps - before_dps
        return gain / resin_cost >= 0.1
