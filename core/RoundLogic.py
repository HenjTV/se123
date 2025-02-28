import random
from classes.character import characters
from skill.skills import skills, NoctisCurse, NoctisHealingReduction, NoctisDamageReduction, LightforgeBlessing, NoctisBloodPact
from skill.debuffs import NoctisCurseDebuff, NoctisHealingReductionDebuff, NoctisDamageReductionDebuff
from skill.buffs import LightforgeBlessingBuff, BloodPactBuff

class Player:
    def __init__(self, character):
        self.character = character
        self.maxHP = character["maxHP"]
        self.maxPowerBar = character["maxPowerBar"]
        self.resourceType = character["resourceType"]
        self.resourceMaxValue = character["resourceMaxValue"]
        self.baseBreak = character["baseBreak"]
        
        self.currentAttackPower = character["AttackPower"]
        self.currentDefencePower = character["DefencePower"]
        self.currentParryPower = character["ParryPower"]
        self.currentKickPower = character["KickPower"]
        self.currentHealPower = character["HealPower"]
        self.currentHP = self.maxHP
        self.currentPowerBar = 0
        self.currentArmour = character["Armour"]
        self.currentBreak = character["baseBreak"]
        self.currentCounterDamage = character["CounterDamage"]
        self.currentResource = character["resourceBaseValue"]
        self.currentResourceRegen = character["ResourceRegen"]
        
        self.blockedAttack = 0
        self.blockedDefence = 0
        self.blockedParry = 0
        self.blockedKick = 0
        self.blockedHeal = 0
        self.skill_cooldowns = {}
        
        self.canBeBlockedAttack = False
        self.canBeBlockedDefence = True
        self.canBeBlockedParry = False
        self.canBeBlockedKick = False
        self.canBeBlockedHeal = True
        
        self.canBeInterruptedAttack = False
        self.canBeInterruptedDefence = True
        self.canBeInterruptedParry = False
        self.canBeInterruptedKick = False
        self.canInterruptedHeal = True
        
        self.roundBaseDamage = 0
        self.roundTrueDamage = 0
        self.roundTrueHeal = 0
        self.roundBaseHeal = 0
        self.roundBaseParry = 0
        self.roundDeadly = 0
        self.roundArmour = 0
        self.roundBreak = 0
        self.roundDamage = 0
        self.roundHeal = 0
        self.roundInterrupt = 0
        self.roundResourceSpended = 0
        self.damage_modifier = 1.0
        self.heal_modifier = 1.0
        self.enemy = None
        self.action = None
        
        self.selected_skills = []
        self.active_buffs = {}
        self.active_debuffs = {}
        self.total_healing_reduction = 0
        self.pending_effects = []

    def set_skill(self, skill_id, level=1):
        skill_data = skills.get(int(skill_id))
        if skill_data:
            skill = skill_data.__class__(level=level)
            for existing_skill in self.selected_skills:
                if existing_skill.base_action == skill.base_action:
                    old_level = existing_skill.level
                    existing_skill.level = level
                    print(f"[{self.character['name']}] Upgraded '{skill.name}' from Lv.{old_level} to Lv.{level}")
                    return
            self.selected_skills.append(skill)
            if skill.base_action not in self.skill_cooldowns:
                self.skill_cooldowns[skill.base_action] = 0
            print(f"[{self.character['name']}] Selected '{skill.display_name}'")
        else:
            print(f"[{self.character['name']}] Error: No skill found for ID {skill_id}")

    def apply_skill(self, enemy):
        if not self.selected_skills:
            return False
        
        success = False
        for skill in self.selected_skills:
            if skill.base_action == self.action:
                cooldown = self.skill_cooldowns.get(skill.base_action, 0)
                if cooldown > 0:
                    print(f"[{self.character['name']}] '{skill.display_name}' on cooldown ({cooldown} rounds left)")
                    continue
                success = skill.apply(self, enemy)
                base_cooldown = skill.cooldown
                enemy_break = enemy.roundBreak if enemy.roundBreak > 0 else 0
                self.skill_cooldowns[skill.base_action] = max(base_cooldown, enemy_break)
                break
        return success

    def add_buff(self, buff):
        if buff.name in self.active_buffs:
            existing = self.active_buffs[buff.name]
            if buff.can_stack and existing["stacks"] < buff.max_stacks:
                existing["stacks"] += 1
                print(f"[{self.character['name']}] Stacked '{buff.name}' (Lv.{buff.skill.level if buff.skill else 1}): Stacks={existing['stacks']}")
            if buff.refresh_duration:
                existing["duration"] = buff.duration
                existing["visual_duration"] = buff.duration
                existing["instance"].refresh_effect()
            existing["level"] = buff.skill.level if buff.skill else 1
            existing["instance"].skill.level = buff.skill.level if buff.skill else 1
            existing["instance"].refresh_effect()
        else:
            self.active_buffs[buff.name] = {
                "duration": buff.duration,
                "visual_duration": buff.duration,
                "instance": buff,
                "trigger_conditions": buff.trigger_conditions,
                "effect_applied": False,
                "buff_applied_this_round": False,
                "stacks": 1,
                "level": buff.skill.level if buff.skill else 1
            }
            print(f"[{self.character['name']}] Added '{buff.name}' (Lv.{buff.skill.level if buff.skill else 1}): Duration={buff.duration}")

    def add_debuff(self, debuff):
        if debuff.name in self.active_debuffs:
            existing = self.active_debuffs[debuff.name]
            if debuff.can_stack and existing["stacks"] < debuff.max_stacks:
                existing["stacks"] += 1
                print(f"[{self.character['name']}] Stacked '{debuff.name}' (Lv.{debuff.skill.level if debuff.skill else 1}): Stacks={existing['stacks']}")
            if debuff.refresh_duration:
                existing["duration"] = debuff.duration
                existing["visual_duration"] = debuff.duration
                existing["instance"].refresh_effect()
            existing["level"] = debuff.skill.level if debuff.skill else 1
            existing["instance"].skill.level = debuff.skill.level if debuff.skill else 1
            existing["instance"].max_stacks = debuff.effect["max_stacks"]
            existing["instance"].refresh_effect()
        else:
            self.active_debuffs[debuff.name] = {
                "duration": debuff.duration,
                "visual_duration": debuff.duration,
                "instance": debuff,
                "trigger_conditions": debuff.trigger_conditions,
                "effect_applied": False,
                "buff_applied_this_round": False,
                "stacks": debuff.stacks,
                "level": debuff.skill.level if debuff.skill else 1
            }
            print(f"[{self.character['name']}] Added '{debuff.name}' (Lv.{debuff.skill.level if debuff.skill else 1}): Duration={debuff.duration}")

    def process_effects(self, enemy):
        self.total_healing_reduction = 0
        self.damage_modifier = 1.0
        self.heal_modifier = 1.0
        for buff_data in self.active_buffs.values():
            buff_data["buff_applied_this_round"] = False
        for debuff_data in self.active_debuffs.values():
            debuff_data["buff_applied_this_round"] = False

        for debuff_name, data in list(self.active_debuffs.items()):
            debuff = data["instance"]
            if not data["trigger_conditions"] or self.action in data["trigger_conditions"]:
                debuff.apply(self)
                data["buff_applied_this_round"] = True

        for buff_name, data in list(self.active_buffs.items()):
            buff = data["instance"]
            if self.action in data["trigger_conditions"]:
                buff.apply(self)
                if "damage_boost" in buff.effect:
                    self.damage_modifier *= (1 + buff.effect["damage_boost"] / 100)
                    data["buff_applied_this_round"] = True
                if "heal_boost" in buff.effect:
                    self.heal_modifier *= (1 + buff.effect["heal_boost"])
                    data["buff_applied_this_round"] = True

        self.roundBaseDamage *= self.damage_modifier
        self.roundBaseHeal *= self.heal_modifier

    def update_buffs_debuffs(self):
        for buff_name, data in list(self.active_buffs.items()):
            if data["buff_applied_this_round"] and data["instance"].expire_on_apply:
                del self.active_buffs[buff_name]
                print(f"[{self.character['name']}] '{buff_name}' expired (expire_on_apply)")
            elif data["duration"] != float('inf'):
                data["duration"] -= 1
                data["visual_duration"] -= 1
                if data["duration"] <= 0:
                    del self.active_buffs[buff_name]
                    print(f"[{self.character['name']}] '{buff_name}' expired")

        for debuff_name, data in list(self.active_debuffs.items()):
            if data["buff_applied_this_round"] and data["instance"].expire_on_apply:
                del self.active_debuffs[debuff_name]
                print(f"[{self.character['name']}] '{debuff_name}' expired (expire_on_apply)")
            elif data["duration"] != float('inf'):
                data["duration"] -= 1
                data["visual_duration"] -= 1
                if data["duration"] <= 0:
                    del self.active_debuffs[debuff_name]
                    print(f"[{self.character['name']}] '{debuff_name}' expired")

    def load_effects(self, debuffs_data, opponent_skills=None):
        debuff_classes = {
            "NoctisCurseDebuff": NoctisCurseDebuff,
            "NoctisHealingReductionDebuff": NoctisHealingReductionDebuff,
            "NoctisDamageReductionDebuff": NoctisDamageReductionDebuff
        }
        self.active_debuffs = {}
        for name, data in debuffs_data.items():
            debuff_class = debuff_classes.get(name)
            if debuff_class:
                level = data.get("level", 1)
                skill = None
                if name == "NoctisCurseDebuff":
                    skill = NoctisCurse(level=level)
                elif name == "NoctisHealingReductionDebuff":
                    skill = NoctisHealingReduction(level=level)
                elif name == "NoctisDamageReductionDebuff":
                    skill = NoctisDamageReduction(level=level)
                debuff = debuff_class(skill=skill)
                self.active_debuffs[name] = {
                    "duration": data["duration"],
                    "visual_duration": data.get("visual_duration", data["duration"]),
                    "instance": debuff,
                    "trigger_conditions": data.get("trigger_conditions", []),
                    "effect_applied": data.get("effect_applied", False),
                    "buff_applied_this_round": False,
                    "stacks": data.get("stacks", 1),
                    "level": level,
                    "max_stacks": data.get("max_stacks", debuff.max_stacks)
                }

    def load_buffs(self, buffs_data, opponent_skills=None):
        buff_classes = {
            "LightforgeBlessingBuff": LightforgeBlessingBuff,
            "BloodPactBuff": BloodPactBuff
        }
        self.active_buffs = {}
        for name, data in buffs_data.items():
            buff_class = buff_classes.get(data["name"])
            if buff_class:
                level = data.get("level", 1)
                skill = None
                if name == "LightforgeBlessingBuff":
                    skill = LightforgeBlessing(level=level)
                elif name == "BloodPactBuff":
                    skill = NoctisBloodPact(level=level)
                buff = buff_class(skill=skill)
                self.active_buffs[name] = {
                    "duration": data["duration"],
                    "visual_duration": data.get("visual_duration", data["duration"]),
                    "instance": buff,
                    "trigger_conditions": data.get("trigger_conditions", []),
                    "effect_applied": data.get("effect_applied", False),
                    "buff_applied_this_round": False,
                    "stacks": data.get("stacks", 1),
                    "level": level
                }

    def playerClearVariables(self):
        self.roundBaseDamage = 0
        self.roundTrueDamage = 0
        self.roundTrueHeal = 0
        self.roundBaseHeal = 0
        self.roundBaseParry = 0
        self.roundDeadly = 0
        self.roundArmour = 0
        self.roundBreak = 0
        self.roundDamage = 0
        self.roundHeal = 0
        self.roundInterrupt = 0
        self.roundResourceSpended = 0
        self.damage_modifier = 1.0
        self.heal_modifier = 1.0

    def blockedUpdate(self):
        self.blockedAttack = max(0, self.blockedAttack - 1)
        self.blockedDefence = max(0, self.blockedDefence - 1)
        self.blockedParry = max(0, self.blockedParry - 1)
        self.blockedKick = max(0, self.blockedKick - 1)
        self.blockedHeal = max(0, self.blockedHeal - 1)
        for action in self.skill_cooldowns:
            self.skill_cooldowns[action] = max(0, self.skill_cooldowns[action] - 1)

    def calculate_roundBreak(self, action):
        self.roundBreak = 0
        if action == "Kick" and not any(skill.base_action == "Kick" for skill in self.selected_skills):
            self.roundBreak = self.currentBreak
        elif any(skill.base_action == "Kick" and self.skill_cooldowns.get(skill.base_action, 0) == 0 for skill in self.selected_skills):
            self.apply_skill(self.enemy)

    def calculate_roundBreakAmplify(self, action):
        if self.enemy.roundBreak > 0:
            if self.canBeBlockedAttack and action == "Attack":
                self.blockedAttack = self.enemy.roundBreak
            if self.canBeBlockedDefence and action == "Defence":
                self.blockedDefence = self.enemy.roundBreak
            if self.canBeBlockedParry and action == "Parry":
                self.blockedParry = self.enemy.roundBreak
            if self.canBeBlockedKick and action == "Kick":
                self.blockedKick = self.enemy.roundBreak
            if self.canBeBlockedHeal and action == "Heal":
                self.blockedHeal = self.enemy.roundBreak

    def calculate_spended_resources(self, action):
        self.roundResourceSpended = self.currentPowerBar

    def calculate_resource_spend(self, action):
        if self.resourceType in ["Energy", "Mana", "Rage", "Focus"]:
            self.currentResource = max(0, self.currentResource - self.currentPowerBar)

    def calculate_resource_passive_bonuses(self, action):
        if self.resourceType == "Rage":
            self.roundBaseDamage += self.roundResourceSpended
        elif self.resourceType == "ColdBlood":
            if self.currentResource >= 50:
                self.roundBaseDamage += self.roundResourceSpended * 2
                self.currentBreak = self.baseBreak
            elif self.currentResource < 50:
                self.currentBreak += 1
                self.roundBaseHeal += self.roundResourceSpended * 2

    def calculate_resource_active_bonuses(self, action):
        if self.resourceType == "Rage":
            self.roundResourceSpended += self.roundResourceSpended
        elif self.resourceType == "Mana" and self.currentPowerBar > self.resourceMaxValue / 2:
            self.roundResourceSpended += self.roundResourceSpended
        elif self.resourceType == "Focus" and self.currentPowerBar > 30 and self.currentPowerBar <= 50:
            self.roundResourceSpended += self.roundResourceSpended
        elif self.resourceType == "Focus" and self.currentPowerBar > 50:
            self.roundResourceSpended += self.roundResourceSpended * 2

    def calculate_resource_regen(self, action):
        if self.resourceType == "Energy":
            self.currentResource = self.currentResource + self.currentResourceRegen
        elif self.resourceType == "Rage":
            self.currentResource = self.currentResource + (self.roundDamage + self.enemy.roundDamage) / 100 * self.currentResourceRegen
        elif self.resourceType == "Mana":
            if self.roundHeal > 0:
                self.currentResource = self.currentResource + self.currentResourceRegen
        elif self.resourceType == "ColdBlood":
            if action in ["Attack", "Kick"]:
                self.currentResource = min(100, self.currentResource + self.currentResourceRegen)
            elif action in ["Defence", "Heal"]:
                self.currentResource = max(0, self.currentResource - self.currentResourceRegen)
            elif action == "Parry":
                if self.currentResource >= 50:
                    self.currentResource += self.currentResourceRegen
                elif self.currentResource < 50:
                    self.currentResource -= self.currentResourceRegen
        elif self.resourceType == "Focus":
            if self.enemy.roundDamage > 0:
                self.currentResource -= self.currentResourceRegen
            elif self.enemy.roundDamage <= 0:
                self.currentResource += self.currentResourceRegen
        self.currentResource = min(self.currentResource, self.resourceMaxValue)

    def calculate_round_damage(self, action):
        if action == "Defence":
            if self.enemy and self.enemy.action in ["Attack", "Parry"]:
                self.roundBaseDamage = self.currentDefencePower + (self.currentDefencePower / 100) * self.roundResourceSpended
            else:
                self.roundBaseDamage = 0
        elif action == "Attack":
            self.roundBaseDamage = self.currentAttackPower + (self.currentAttackPower / 100) * self.roundResourceSpended
            if any(skill.base_action == "Attack" and self.skill_cooldowns.get(skill.base_action, 0) == 0 for skill in self.selected_skills):
                self.apply_skill(self.enemy)
        elif action == "Kick":
            self.roundBaseDamage = self.currentKickPower + (self.currentKickPower / 100) * self.roundResourceSpended
            if any(skill.base_action == "Kick" and self.skill_cooldowns.get(skill.base_action, 0) == 0 for skill in self.selected_skills):
                self.apply_skill(self.enemy)
        else:
            self.roundBaseDamage = 0

    def calculate_round_parry(self, action):
        if action == "Parry":
            self.roundBaseParry = self.enemy.roundBaseDamage * 0.5 * (100 + self.currentCounterDamage) / 100
            if any(skill.base_action == "Parry" and self.skill_cooldowns.get(skill.base_action, 0) == 0 for skill in self.selected_skills):
                self.apply_skill(self.enemy)
        else:
            self.roundBaseParry = 0

    def calculate_round_heal(self, action):
        if action == "Heal":
            self.roundBaseHeal = self.currentHealPower + (self.currentHealPower / 100) * self.roundResourceSpended
            if any(skill.base_action == "Heal" and self.skill_cooldowns.get(skill.base_action, 0) == 0 for skill in self.selected_skills):
                self.apply_skill(self.enemy)
            if self.blockedHeal != 0:
                self.roundBaseHeal = 0

    def calculate_round_truedamage(self, action):
        pass

    def calculate_round_trueheal(self, action):
        self.roundTrueHeal = 0

    def calculate_round_armour(self, action):
        if action == "Defence":
            if self.blockedDefence > 0:
                self.roundArmour = 0
            else:
                self.roundArmour = 100 + self.currentArmour
        elif action == "Parry":
            self.roundArmour = 50 + self.currentArmour
        else:
            self.roundArmour = self.currentArmour

    def calculate_round_deadly(self, action):
        if action in ["Attack", "Kick"]:
            self.roundDeadly = 100
        else:
            self.roundDeadly = 0

    def calculate_damage(self, action):
        damage_reduction = sum(
            debuff["instance"].effect.get("damage_reduction", 0) * debuff["stacks"]
            for debuff in self.active_debuffs.values()
            if "damage_reduction" in debuff["instance"].effect
        )
        base_damage = (self.roundBaseDamage + self.roundBaseParry) * (100 - self.enemy.roundArmour) / 100
        if self.blockedAttack > 0 and action == "Attack":
            self.roundDamage = 0
        elif self.blockedDefence > 0 and action == "Defence":
            self.roundDamage = 0
        elif self.blockedParry > 0 and action == "Parry":
            self.roundDamage = 0
        elif self.blockedKick > 0 and action == "Kick":
            self.roundDamage = 0
        else:
            self.roundDamage = base_damage * (100 - damage_reduction) / 100
            print(f"[{self.character['name']}] Dealt {self.roundDamage:.1f} damage: {self.roundBaseDamage:.1f} from {action}, {self.roundBaseParry:.1f} from parry (Reduced by {damage_reduction}%)")

    def calculate_heal(self, action):
        if self.blockedHeal != 0 or self.enemy.action in ["Attack", "Kick"]:
            self.roundHeal = 0
        else:
            self.roundHeal = (self.roundBaseHeal * (100 - self.enemy.roundDeadly) / 100 + self.roundTrueHeal) * (100 - self.total_healing_reduction) / 100
            print(f"[{self.character['name']}] Healed {self.roundHeal:.1f}: {self.roundBaseHeal:.1f} from {action} (Reduced by {self.total_healing_reduction}%)")

    def calculate_currentHP(self, action):
        damage_taken = (self.enemy.roundDamage + self.roundTrueDamage - self.roundHeal) * ((95 + random.random() * 10) / 100)
        self.currentHP -= damage_taken
        self.currentHP = min(self.currentHP, self.maxHP)
        print(f"[{self.character['name']}] HP updated to {self.currentHP:.1f}: Took {self.enemy.roundDamage:.1f} damage, {self.roundTrueDamage:.1f} true damage, Healed {self.roundHeal:.1f}")

    def clearPlayerPowerBar(self):
        self.currentPowerBar = 0

def game_round(p1, p2, p1_action, p2_action):
    p1.enemy = p2
    p2.enemy = p1
    
    print(f"[Round] {p1.character['name']} ({p1_action}) vs {p2.character['name']} ({p2_action})")
    
    p1.playerClearVariables()
    p2.playerClearVariables()

    p1.action = p1_action
    p2.action = p2_action

    p1.calculate_spended_resources(p1_action)
    p2.calculate_spended_resources(p2_action)
    p1.calculate_resource_active_bonuses(p1_action)
    p2.calculate_resource_active_bonuses(p2_action)
    p1.calculate_resource_passive_bonuses(p1_action)
    p2.calculate_resource_passive_bonuses(p2_action)
    p1.calculate_resource_spend(p1_action)
    p2.calculate_resource_spend(p2_action)

    p1.calculate_roundBreak(p1_action)
    p2.calculate_roundBreak(p2_action)
    
    p1.calculate_roundBreakAmplify(p1_action)
    p2.calculate_roundBreakAmplify(p2_action)

    p1.calculate_round_damage(p1_action)
    p2.calculate_round_damage(p2_action)
    
    p1.calculate_round_parry(p1_action)
    p2.calculate_round_parry(p2_action)
    
    p1.calculate_round_heal(p1_action)
    p2.calculate_round_heal(p2_action)
    
    p1.process_effects(p2)
    p2.process_effects(p1)

    p1.calculate_round_truedamage(p1_action)
    p2.calculate_round_truedamage(p2_action)
    
    p1.calculate_round_trueheal(p1_action)
    p2.calculate_round_trueheal(p2_action)
    
    p1.calculate_round_armour(p1_action)
    p2.calculate_round_armour(p2_action)
   
    p1.calculate_damage(p1_action)
    p2.calculate_damage(p2_action)
    
    p1.calculate_heal(p1_action)
    p2.calculate_heal(p2_action)
    
    p1.calculate_currentHP(p1_action)
    p2.calculate_currentHP(p2_action)
    
    p1.calculate_resource_regen(p1_action)
    p2.calculate_resource_regen(p2_action)

    p1.action = None
    p2.action = None
    p1.clearPlayerPowerBar()
    p2.clearPlayerPowerBar()
    
    p1.update_buffs_debuffs()
    p2.update_buffs_debuffs()
    
    p1.blockedUpdate()
    p2.blockedUpdate()
    
    print(f"[Round] Ended: {p1.character['name']} HP={p1.currentHP:.1f}, {p2.character['name']} HP={p2.currentHP:.1f}")
    return True

effect_rules = {
    ('Attack', 'Attack'): True,
    ('Attack', 'Defence'): True,
    ('Attack', 'Parry'): True,
    ('Attack', 'Kick'): True,
    ('Attack', 'Heal'): True,
    ('Attack', 'Idle'): True,
    ('Defence', 'Defence'): True,
    ('Defence', 'Parry'): True,
    ('Defence', 'Kick'): True,
    ('Defence', 'Heal'): True,
    ('Defence', 'Idle'): True,
    ('Parry', 'Parry'): True,
    ('Parry', 'Kick'): True,
    ('Parry', 'Heal'): True,
    ('Parry', 'Idle'): True,
    ('Kick', 'Kick'): True,
    ('Kick', 'Heal'): True,
    ('Kick', 'Idle'): True,
    ('Heal', 'Heal'): True,
    ('Heal', 'Idle'): True,
    ('Idle', 'Idle'): True,
}

def resolve_round(p1, p2, p1_action, p2_action):
    func = effect_rules.get((p1_action, p2_action))
    if func:
        game_round(p1, p2, p1_action, p2_action)
    else:
        game_round(p2, p1, p2_action, p1_action)