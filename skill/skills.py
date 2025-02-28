from skill.buffs import LightforgeBlessingBuff, BloodPactBuff
from skill.debuffs import NoctisCurseDebuff, NoctisHealingReductionDebuff, NoctisDamageReductionDebuff

class Skill:
    def __init__(self, name, base_action, cooldown, level=1, blocked_against=None, 
                 buff_class=None, debuff_class=None, base_effect=None, level_scaling=None):
        self.id = None
        self.name = name
        self.base_action = base_action
        self.cooldown = cooldown
        self.level = level
        self.display_name = f"{self.name}[{self.level}]"
        self.blocked_against = blocked_against or []
        self.buff_class = buff_class
        self.debuff_class = debuff_class
        self.base_effect = base_effect or {}
        self.level_scaling = level_scaling or {
            "base": 1.0,
            "buff": 1.0,
            "debuff": 1.0
        }

    def get_effect(self):
        scale = self.level_scaling["base"]
        multiplier = scale * (1 + (self.level - 1) * 0.2)
        effect = {k: v * multiplier for k, v in self.base_effect.items()}
        return effect

    def get_scaling(self):
        return self.level_scaling

    def apply(self, player, enemy):
        if not self.can_apply(enemy):
            print(f"[{player.character['name']}] '{self.display_name}' blocked by {enemy.action}")
            return False

        if self.base_effect:
            self._apply_base_effect(player, enemy)

        if self.buff_class:
            buff = self.buff_class(skill=self)
            player.add_buff(buff)

        if self.debuff_class:
            debuff = self.debuff_class(skill=self)
            enemy.add_debuff(debuff)

        print(f"[{player.character['name']}] Applied '{self.display_name}' to {enemy.character['name']}")
        return True

    def _apply_base_effect(self, player, enemy):
        effect = self.get_effect()
        if "true_damage" in effect:
            true_damage = enemy.currentHP * effect["true_damage"]
            enemy.roundTrueDamage += true_damage
            print(f"[{enemy.character['name']}] '{self.display_name}' dealt {true_damage:.1f} true damage")
        elif "heal_boost" in effect:
            player.roundBaseHeal *= (1 + effect["heal_boost"])
            if player.resourceType == "Mana":
                player.currentResource = min(player.resourceMaxValue, player.currentResource + player.currentResourceRegen)
            print(f"[{player.character['name']}] '{self.display_name}' boosted heal to {player.roundBaseHeal:.1f}")

    def can_apply(self, enemy):
        return enemy.action not in self.blocked_against

class NoctisCurse(Skill):
    def __init__(self, level=1):
        super().__init__(
            name="Noctis Curse",
            base_action="Attack",
            cooldown=3,
            level=level,
            blocked_against=["Defence"],
            debuff_class=NoctisCurseDebuff,
            base_effect={"true_damage": 0.02143},
            level_scaling={"base": 1.0, "debuff": 1.0, "buff": 1.0, "duration": 0.0, "max_stacks": 0.0}
        )
        
    def _apply_base_effect(self, player, enemy):
        pass

class NoctisHealingReduction(Skill):
    def __init__(self, level=1):
        super().__init__(
            name="Healing Decay",
            base_action="Kick",
            cooldown=3,
            level=level,
            blocked_against=["Defence", "Kick", "Parry", "Attack", "Idle"],
            debuff_class=NoctisHealingReductionDebuff,
            base_effect={},
            level_scaling={"base": 1.0, "debuff": 1.4, "buff": 1.0, "duration": 0.0, "max_stacks": 0.0}
        )

class NoctisDamageReduction(Skill):
    def __init__(self, level=1):
        super().__init__(
            name="Parry Mastery",
            base_action="Parry",
            cooldown=2,
            level=level,
            blocked_against=["Defence", "Heal", "Parry", "Idle"],
            debuff_class=NoctisDamageReductionDebuff,
            base_effect={},
            level_scaling={"base": 1.0, "debuff": 1.3, "buff": 1.0, "duration": 0.0, "max_stacks": 0.0}
        )

class LightforgeBlessing(Skill):
    def __init__(self, level=1):
        super().__init__(
            name="Lightforge Blessing",
            base_action="Heal",
            cooldown=5,
            level=level,
            blocked_against=["Kick"],
            buff_class=LightforgeBlessingBuff,
            base_effect={"heal_boost": 0.1},
            level_scaling={"base": 1.2, "buff": 1.35, "debuff": 1.0, "duration": 0.0}
        )

class NoctisBloodPact(Skill):
    def __init__(self, level=1):
        super().__init__(
            name="Blood Pact",
            base_action="Heal",
            cooldown=0,
            level=level,
            blocked_against=["Attack"],
            buff_class=BloodPactBuff,
            base_effect={"heal": 30},
            level_scaling={"base": 1.0, "buff": 1.7857, "debuff": 1.0, "duration": 0.0, "damage_self": 1.7857}
        )

    def _apply_base_effect(self, player, enemy):
        effect = self.get_effect()
        heal_amount = effect["heal"] + (self.level - 1) * 15
        player.roundBaseHeal += heal_amount
        print(f"[{player.character['name']}] '{self.display_name}' healed for {heal_amount:.1f}")

skills = {
    1: NoctisCurse(),
    2: NoctisHealingReduction(),
    3: NoctisDamageReduction(),
    4: LightforgeBlessing(),
    5: NoctisBloodPact()
}
for id, skill in skills.items():
    skill.id = str(id)