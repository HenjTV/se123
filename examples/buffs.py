{
    "name": "LightforgeBlessingBuff",
    "duration": 3,
    "visual_duration": 3,
    "image": "/static/image/superability/lightforge_blessing.jpg",
    "skill": "[Reference to LightforgeBlessing object with level 2]",
    "effect": {
        "damage_boost": 2.3625,  // 1.75 * 1.35 * (1 + 0.2 * (2-1))
        "heal_boost": 0.135      // 0.1 * 1.35 * (1 + 0.2 * (2-1))
    },
    "trigger_conditions": ["Attack"],
    "can_stack": false,
    "refresh_duration": false,
    "expire_on_apply": true,
    "stacks": 1
}