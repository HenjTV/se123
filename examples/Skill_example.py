{
    "name": "Noctis Curse",
    "base_action": "Attack",
    "cooldown": 3,
    "level": 2,
    "display_name": "Noctis Curse[2]",
    "blocked_against": ["Defence"],
    "buff_class": null,
    "debuff_class": "[Reference to NoctisCurseDebuff class]",
    "base_effect": {
        "true_damage": 0.03
    },
    "current_effect": {
        "true_damage": 0.054  // 0.03 * 1.5 * (1 + 0.2 * (2-1))
    },
    "level_scaling": {
        "base": 1.5,
        "buff": 1.0,
        "debuff": 1.5
    }
}