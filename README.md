# DroidPilot

Use AI to control your Android phone — with natural language.

```bash
droidpilot "Open Settings and enable Dark Mode"
```

...and watch AI run on your device. Because your thumbs deserve a break.

## What is this?

DroidPilot is an AI agent that reads your Android screen's accessibility tree and performs actions like tapping, swiping, and typing — all from a single natural language prompt.

No screenshots. No computer vision. Just the structured UI tree that Android already provides, fed into an LLM that decides what to do next.

```
You say: "Open Chrome and search for weather in Tokyo"

DroidPilot:
  Step 1: tap(ref=5)          → Taps Chrome icon
  Step 2: tap(ref=2)          → Taps search bar
  Step 3: type_text(ref=2)    → Types "weather in Tokyo"
  Step 4: press_enter()       → Submits search
  Step 5: done()              → "Searched for weather in Tokyo in Chrome"
```

## How it works

```
┌──────────┐     ADB: uiautomator dump     ┌──────────────┐
│  Android  │ ──────────────────────────── → │  UI XML Tree  │
│  Device   │                                └──────┬───────┘
│           │     ADB: input tap/swipe/text         │ parse into
│           │ ◄ ──────────────────────────── ┐      ▼
└──────────┘                                 │  ┌──────────┐
                                             │  │ Readable  │
                                             │  │ Text Tree │
                                             │  │ + ref_map │
                                             │  └────┬─────┘
                                             │       │
                                             │       ▼
                                             │  ┌──────────┐
                                             │  │  LLM     │
                                             │  │ (GPT-4o) │
                                             │  └────┬─────┘
                                             │       │
                                             │  tool call:
                                             │  tap(ref=3)
                                             │       │
                                             └───────┘
```

The agent runs in a loop — read screen, ask the LLM, execute action, repeat — until the task is done or it hits the step limit.

## Setup

### Prerequisites

- Python 3.10+
- ADB installed (`brew install android-platform-tools` on macOS)
- An Android device connected via USB with USB debugging enabled
- An OpenAI API key

### Install

```bash
git clone https://github.com/Aditya8840/droidpilot.git
cd droidpilot
pip install .
```

### Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
DROIDPILOT_MODEL=gpt-4o
```

## Usage

```bash
# Basic usage
droidpilot "Open Settings and enable Dark Mode"

# Use a different model
droidpilot "Take a screenshot" --model gpt-4o-mini

# Increase max steps for complex tasks
droidpilot "Open Gmail and compose an email to john" --max-steps 50

# Run as a module
python3 -m droidpilot "Turn off WiFi"
```

## Use cases

**Give hands to your AI coding agent.** If you're building an Android app with an AI coding assistant, DroidPilot can be the testing layer — let the coding agent run your app on a real device and verify the UI works as expected.

**Automate repetitive phone tasks.** Changing settings across multiple devices, filling out forms, navigating deep menus — describe it once and let DroidPilot handle it.

**If you have other use cases, [open an issue](https://github.com/Aditya8840/droidpilot/issues) — I'd love to hear about it.**

## License

MIT
