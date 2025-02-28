{
    "name": "NoctisCurseDebuff",
    "duration": 5,
    "visual_duration": 5,
    "image": "/static/image/superskill/noctis_curse.jpg",
    "skill": "[Reference to NoctisCurse object with level 2]",
    "effect": {
        "true_damage": 0.054  // 0.03 * 1.5 * (1 + 0.2 * (2-1))
    },
    "trigger_conditions": [],
    "can_stack": true,
    "refresh_duration": true,
    "expire_on_apply": false,
    "stacks": 2,
    "max_stacks": 5
}