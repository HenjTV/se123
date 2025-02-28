{
    "character": {
        "name": "Noctis",
        "AttackPower": 120,
        "DefencePower": 60,
        "ParryPower": 110,
        "KickPower": 60,
        "HealPower": 40,
        "maxHP": 1050,
        "maxPowerBar": 30,
        "resourceType": "Energy",
        "resourceMaxValue": 50,
        "resourceBaseValue": 35,
        "baseBreak": 3,
        "Armour": 0,
        "CounterDamage": 55,
        "ResourceRegen": 18,
        "skills": { "1": 1, "2": 1, "3": 1 },
        "avatarImage": "/static/image/Noctis.jpg",
        "avatarImageNoBg": "/static/image/NoBg/Noctis.png",
        "sound": "/static/sound/Noctis.mp3",
        "gr1": "#54FBAB",
        "gr2": "#097B3D",
        "gr3": "#08130F"
    },
    "maxHP": 1050,
    "maxPowerBar": 30,
    "resourceType": "Energy",
    "resourceMaxValue": 50,
    "currentAttackPower": 120,
    "currentDefencePower": 60,
    "currentParryPower": 110,
    "currentKickPower": 60,
    "currentHealPower": 40,
    "currentHP": 1020,
    "currentPowerBar": 0,
    "currentArmour": 0,
    "currentBreak": 3,
    "currentCounterDamage": 55,
    "currentResource": 45,
    "currentResourceRegen": 18,
    "blockedAttack": 0,
    "blockedDefence": 0,
    "blockedParry": 0,
    "blockedKick": 0,
    "blockedHeal": 0,
    "skill_cooldowns": {
        "Attack": 3,
        "Kick": 0,
        "Parry": 0
    },
    "canBeBlockedAttack": false,
    "canBeBlockedDefence": true,
    "canBeBlockedParry": false,
    "canBeBlockedKick": false,
    "canBeBlockedHeal": true,
    "canBeInterruptedAttack": false,
    "canBeInterruptedDefence": true,
    "canBeInterruptedParry": false,
    "canBeInterruptedKick": false,
    "canInterruptedHeal": true,
    "roundBaseDamage": 0,
    "roundTrueDamage": 0,
    "roundTrueHeal": 0,
    "roundBaseHeal": 0,
    "roundBaseParry": 0,
    "roundDeadly": 0,
    "roundArmour": 0,
    "roundBreak": 0,
    "roundDamage": 0,
    "roundHeal": 0,
    "roundInterrupt": 0,
    "roundResourceSpended": 0,
    "damage_modifier": 1.0,
    "heal_modifier": 1.0,
    "enemy": "[Reference to another Player object]",
    "action": "Idle",
    "selected_skills": [
        {
            "id": "1",
            "level": 1,
            "base_action": "Attack"
        },
        {
            "id": "2",
            "level": 1,
            "base_action": "Kick"
        },
        {
            "id": "3",
            "level": 1,
            "base_action": "Parry"
        }
    ],
    "active_buffs": {},
    "active_debuffs": {
        "NoctisCurseDebuff": {
            "duration": 5,
            "visual_duration": 5,
            "instance": "[Reference to NoctisCurseDebuff object]",
            "trigger_conditions": [],
            "effect_applied": false,
            "buff_applied_this_round": false,
            "stacks": 1
        }
    },
    "total_healing_reduction": 0,
    "pending_effects": []
}