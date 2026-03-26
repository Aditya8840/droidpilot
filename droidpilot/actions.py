TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tap",
            "description": "Tap on a UI element by its ref ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "integer",
                        "description": "The ref ID of the element to tap (e.g., 3 for [3])",
                    },
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Tap on a text field by ref ID to focus it, then type the given text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "integer",
                        "description": "The ref ID of the text field to type into",
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type",
                    },
                },
                "required": ["ref", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "swipe",
            "description": "Swipe/scroll the screen in a direction. 'up' scrolls content down, 'down' scrolls content up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "left", "right"],
                        "description": "Direction to swipe",
                    },
                },
                "required": ["direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_back",
            "description": "Press the Android back button.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_home",
            "description": "Press the Android home button.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_enter",
            "description": "Press Enter/Return key.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch an app by its package name (e.g., 'com.android.settings').",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {
                        "type": "string",
                        "description": "The Android package name of the app to launch",
                    },
                },
                "required": ["package_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait for the UI to settle after a screen transition or loading.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {
                        "type": "integer",
                        "description": "Number of seconds to wait (1-10)",
                        "default": 2,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_apps",
            "description": "List installed app package names. Optionally filter by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Optional filter string to match against package names (e.g., 'chrome', 'settings')",
                        "default": "",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that the task is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A brief summary of what was accomplished",
                    },
                },
                "required": ["summary"],
            },
        },
    },
]
