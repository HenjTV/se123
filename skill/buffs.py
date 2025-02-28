from abc import ABC, abstractmethod

class Buff(ABC):
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

    @abstractmethod
    def apply(self, player):
        pass

    def get_effect(self):
        base_effect = self.get_default_effect()
        if self.skill:
            scaling = self.skill.get_scaling()
            scaled_effect = {}
            for key, value in base_effect.items():
                scale = scaling.get(key, scaling["buff"])
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

    def get_default_effect(self):
        return {}

class LightforgeBlessingBuff(Buff):
    def __init__(self, skill=None):
        super().__init__(
            skill=skill,
            trigger_conditions=["Attack"],
            can_stack=False,
            refresh_duration=False,
            expire_on_apply=True
        )
        self.image = "/static/image/superability/lightforge_blessing.jpg"

    def apply(self, player):
        print(f"[{player.character['name']}] Applied '{self.name}' (Lv.{self.skill.level if self.skill else 1}): {self.effect['damage_boost']}% damage boost, {self.effect['heal_boost']}% heal boost")

    def get_default_effect(self):
        return {
            "damage_boost": 1.75,
            "heal_boost": 0.1,
            "duration": 3
        }

class BloodPactBuff(Buff):
    def __init__(self, skill=None):
        super().__init__(
            skill=skill,
            trigger_conditions=["Attack", "Kick", "Parry", "Defence", "Heal", None],
            can_stack=True,
            refresh_duration=True,
            expire_on_apply=False
        )
        self.image = "/static/image/superskill/blood_pact.jpg"
        self.max_stacks = 5

    def apply(self, player):
        stacks = player.active_buffs[self.name]["stacks"]
        damage_self = player.currentHP * (self.effect["damage_self"] / 100) * stacks
        player.currentHP = max(1, player.currentHP - damage_self)
        total_damage_boost = self.effect["damage_boost"] * stacks
        player.damage_modifier *= (1 + total_damage_boost / 100)
        print(f"[{player.character['name']}] Applied '{self.name}' (Lv.{self.skill.level if self.skill else 1}): {damage_self:.1f} self-damage, {total_damage_boost}% damage boost (Stacks: {stacks})")

    def get_default_effect(self):
        return {
            "damage_boost": 1.7857,
            "damage_self": 0.56,
            "duration": 5,
            "max_stacks": 5
        }

    def get_effect(self):
        base_effect = self.get_default_effect()
        if self.skill:
            scaling = self.skill.get_scaling()
            scaled_effect = {}
            for key, value in base_effect.items():
                scale = scaling.get(key, scaling["buff"])
                if scale == 0 or key == "max_stacks":
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