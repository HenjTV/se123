from abc import ABC, abstractmethod

class Debuff(ABC):
    def __init__(self, duration=None, skill=None, trigger_conditions=None, 
                 can_stack=False, refresh_duration=False, expire_on_apply=False):
        self.image = None
        self.name = self.__class__.__name__
        self.skill = skill
        self.effect = self.get_effect()
        self.duration = self.effect.get("duration", duration)
        self.trigger_conditions = trigger_conditions or []
        self.can_stack = can_stack
        self.refresh_duration = refresh_duration
        self.expire_on_apply = expire_on_apply
        self.stacks = 1
        self.max_stacks = self.effect.get("max_stacks", 5)

    @abstractmethod
    def apply(self, player):
        pass

    def get_effect(self):
        base_effect = self.get_default_effect()
        if self.skill:
            scaling = self.skill.get_scaling()
            scaled_effect = {}
            for key, value in base_effect.items():
                scale = scaling.get(key, scaling["debuff"])
                if scale == 0:
                    scaled_effect[key] = value
                else:
                    multiplier = scale * (1 + (self.skill.level - 1) * 0.2)
                    scaled_effect[key] = value * multiplier
            return scaled_effect
        return base_effect

    def refresh_effect(self):
        self.effect = self.get_effect()
        self.duration = self.effect["duration"]
        self.max_stacks = self.effect["max_stacks"]

    def get_default_effect(self):
        return {}

class NoctisCurseDebuff(Debuff):
    def __init__(self, skill=None):
        super().__init__(
            skill=skill,
            trigger_conditions=[],
            can_stack=True,
            refresh_duration=True,
            expire_on_apply=False
        )
        self.image = "/static/image/superskill/noctis_curse.jpg"

    def apply(self, player):
        stacks = player.active_debuffs[self.name]["stacks"]
        true_damage = player.currentHP * self.effect["true_damage"] * stacks
        player.roundTrueDamage += true_damage
        print(f"[{player.character['name']}] Applied '{self.name}' (Lv.{self.skill.level if self.skill else 1}): {true_damage:.1f} true damage (Stacks: {stacks})")

    def get_default_effect(self):
            return {
                "true_damage": 0.02143,  # Базовый урон
                "duration": 5,
                "max_stacks": 5
            }

class NoctisHealingReductionDebuff(Debuff):
    def __init__(self, skill=None):
        super().__init__(
            skill=skill,
            trigger_conditions=["Heal"],
            can_stack=True,
            refresh_duration=True,
            expire_on_apply=False
        )
        self.image = "/static/image/superskill/noctis_healing_decay.jpg"

    def apply(self, player):
        healing_reduction = self.effect["healing_reduction"] * player.active_debuffs[self.name]["stacks"]
        player.total_healing_reduction = min(100, player.total_healing_reduction + healing_reduction)
        print(f"[{player.character['name']}] Applied '{self.name}' (Lv.{self.skill.level if self.skill else 1}): {healing_reduction}% healing reduction (Total: {player.total_healing_reduction}%)")

    def get_default_effect(self):
        return {
            "healing_reduction": 5,
            "duration": 5,
            "max_stacks": 5
        }

class NoctisDamageReductionDebuff(Debuff):
    def __init__(self, skill=None):
        super().__init__(
            skill=skill,
            trigger_conditions=["Attack", "Kick"],
            can_stack=True,
            refresh_duration=True,
            expire_on_apply=False
        )
        self.image = "/static/image/superskill/noctis_parry_mastery.jpg"

    def apply(self, player):
        print(f"[{player.character['name']}] Applied '{self.name}' (Lv.{self.skill.level if self.skill else 1}): {self.effect['damage_reduction']}% damage reduction")

    def get_default_effect(self):
        return {
            "damage_reduction": 6.923076923076923,
            "duration": 4,
            "max_stacks": 5
        }