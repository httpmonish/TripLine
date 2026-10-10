# Tripline 90-Second Demo Video Pipeline

This directory contains the complete pipeline, raw execution captures, card generators, and encoding scripts for Tripline's official hackathon demo video.

**Video Specifications**:
* **Duration**: Exactly **86.0 seconds** (Hard limit: ≤ 90.0s measured via ffprobe).
* **Resolution**: 1920×1080 (1080p, 30fps).
* **Codecs**: H.264 video (`yuv420p`), AAC audio (`44100Hz`, stereo).
* **Bitrate / Size**:
  * Main Delivery: `video/out/tripline_demo_90s.mp4` (~1.6 MB).
  * Low-Bitrate Delivery: `video/out/tripline_demo_90s_lowbitrate.mp4` (~1.3 MB, optimized for portal uploads < 25 MB).

---

## Directory Structure
* `storyboard.json`: Machine-readable beat timeline, timestamps, durations, and captions.
* `captions.srt`: Synchronized subtitle track for submission portals.
* `voiceover.txt`: Declarative voiceover script (108 words).
* `build.py`: Deterministic video rendering and ffmpeg concatenation script.
* `qa_check.py`: Quality assurance script verifying timing, streams, PII/secrets, and truth matching.
* `cards/`: Rendered 1080p keyframes for title card (`B1.png`) and disclosure card (`B7.png`).
* `capture/`: Raw execution output logs (`*.log`) and `MANIFEST.json` with SHA-256 digests.
* `human_captures/`: Directory reserved for optional platform screenshots (H1/H2/H3).
* `fonts/`: Bundled open-license / standard system fonts (`Courier_New.ttf`, `Arial.ttf`).
* `out/`: Final compiled MP4 video artifacts.

---

## How to Rebuild the Video
To rebuild the video from scratch using the recorded real logs:
```bash
# Run build pipeline
.venv313/bin/python video/build.py

# Run quality assurance checks
.venv313/bin/python video/qa_check.py
```
Or via make:
```bash
make video
```
