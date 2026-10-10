# Tripline Demo Recording & Terminal Capture Guide

**Target Video Duration:** 90 Seconds  
**Measured `make wow` Runtime:** 21.71 seconds (real platform round-trips, zero artificial sleeps)

---

## 1. Terminal Environment Recommendations
- **Terminal Application:** iTerm2, macOS Terminal, or Ghostty
- **Window Dimensions:** 1920x1080 (16:9 aspect ratio) or 120 columns x 36 rows
- **Color Scheme:** Dark Theme (e.g. Dracula, OneDark, Tokyo Night, or Catppuccin Mocha)
- **Font:** JetBrains Mono, Fira Code, or SF Mono at 16pt–18pt (high readability on video)
- **Prompt:** Minimalist prompt (e.g. `tripline $ `) to maximize vertical space

---

## 2. Capture Commands Sequence

### Shot 1: The Full Wow Sequence (Terminal Beat: 0:08–1:20)
Run the automated Makefile target which executes all 5 beats in sequence:
```bash
make wow
```
*Pacing Note:* `make wow` executes completely in 21.71 seconds. In a 90-second video, you can present this unhurriedly or apply subtle 1.25x speedup during the ArmorIQ network round-trips if adding voiceover commentary.

### Shot 2: Tamper Demonstration Standalone (Beat: 1:08–1:20)
To isolate the red `TAMPER_DETECTED` alert for maximum visual punch:
```bash
python scripts/tamper_demo.py
```

### Shot 3: Deterministic Jail Burst Standalone (Beat: 0:50–1:08)
To show the path-trick matrix denying all 7 traversal vectors:
```bash
python scripts/jail_burst.py
```

### Shot 4: Audit Link Chain Verification
```bash
python -m scripts.verify_links
```

---

## 3. Editing and Speedup Guidance
- **No Simulation / No Stubs:** All footage captured from `make wow` runs against live ArmorIQ platform and authentic cryptographic components.
- **Editing Cuts:** Do not cut out the output tables. If pacing runs tight against the 90s limit, trim the 3-second network latency pauses during HTTP handshake, never the resulting output.
