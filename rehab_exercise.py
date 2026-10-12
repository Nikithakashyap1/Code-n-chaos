
EXERCISES = {
    "Finger Flexion": {
        "category": "FINGER MOBILITY",
        "difficulty": "Gentle",
        "target": 10,
        "icon": "✊",
        "description": "Curl your fingers toward your palm, then relax.",
    },
    "Finger Extension": {
        "category": "FINGER MOBILITY",
        "difficulty": "Gentle",
        "target": 10,
        "icon": "🖐",
        "description": "Gently straighten your fingers.",
    },
    "Thumb Opposition": {
        "category": "THUMB CONTROL",
        "difficulty": "Focused",
        "target": 8,
        "icon": "👌",
        "description": "Move your thumb toward each fingertip.",
    },
    "Finger Spreading": {
        "category": "FINGER CONTROL",
        "difficulty": "Gentle",
        "target": 10,
        "icon": "✋",
        "description": "Spread your fingers apart, then bring them together.",
    },
    "Wrist Flexion & Extension": {
        "category": "WRIST MOBILITY",
        "difficulty": "Controlled",
        "target": 8,
        "icon": "↕️",
        "description": "Move your wrist gently forward and backward.",
    },
    "Gentle Hand Opening": {
        "category": "WARM-UP",
        "difficulty": "Gentle",
        "target": 10,
        "icon": "✦",
        "description": "Open a relaxed hand and spread the fingers naturally.",
    },
}

def get_exercise_instructions(name):
    instructions = {
        "Finger Flexion":
            "Slowly curl your fingers toward your palm, pause, then relax.",
        "Finger Extension":
            "Straighten your fingers gently, hold briefly, then relax.",
        "Thumb Opposition":
            "Touch your thumb to each fingertip one at a time.",
        "Finger Spreading":
            "Spread your fingers comfortably, then bring them together.",
        "Wrist Flexion & Extension":
            "Support your forearm and move your wrist within a comfortable range.",
        "Gentle Hand Opening":
            "Open your hand slowly from a relaxed, softly curled position.",
    }
    return instructions.get(name, "Move slowly and comfortably.")
