# Graph Report - super-ai_editor  (2026-11-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 297 nodes · 604 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f350df3b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.py
- package.json
- test_all_services.py
- run.py
- verify_system.py
- realsfx_service.py
- analyze_audio_track
- super_ai_editor
- compilerOptions
- index.ts
- get_library
- export_video
- download_rendered_video

## God Nodes (most connected - your core abstractions)
1. `run_standalone()` - 20 edges
2. `check_ollama_status()` - 17 edges
3. `get_hardware_profile()` - 17 edges
4. `ask_ollama_copilot()` - 16 edges
5. `analyze_audio_track()` - 16 edges
6. `compilerOptions` - 16 edges
7. `render_timeline_project()` - 15 edges
8. `export_srt()` - 15 edges
9. `transcribe_audio_file()` - 15 edges
10. `generate_custom_sfx()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_6_ollama_copilot()` --calls--> `ask_ollama_copilot()`  [EXTRACTED]
  verify_system.py → backend/app/services/ollama_service.py
- `test_6_ollama_copilot()` --calls--> `check_ollama_status()`  [EXTRACTED]
  verify_system.py → backend/app/services/ollama_service.py
- `test_1_hardware_profile()` --calls--> `get_hardware_profile()`  [EXTRACTED]
  verify_system.py → backend/app/services/system_detector.py
- `test_2_realsfx_synthesis()` --calls--> `ensure_default_sfx_library()`  [EXTRACTED]
  verify_system.py → backend/app/services/realsfx_service.py
- `test_2_realsfx_synthesis()` --calls--> `list_sfx_library()`  [EXTRACTED]
  verify_system.py → backend/app/services/realsfx_service.py

## Import Cycles
- None detected.

## Communities (13 total, 3 thin omitted)

### Community 0 - "main.py"
Cohesion: 0.09
Nodes (17): serve_app_js(), serve_spa(), get_thumbnails(), interpolate_frames(), InterpolateRequest, serve_thumbnail(), speed_ramp(), SpeedRampRequest (+9 more)

### Community 1 - "package.json"
Cohesion: 0.07
Nodes (38): dependencies, lucide-react@^1.16.0, react@^19.0.0, react-dom@^19.0.0, three@^0.170.0, devDependencies, autoprefixer@^10.4.19, postcss@^8.4.38 (+30 more)

### Community 2 - "test_all_services.py"
Cohesion: 0.10
Nodes (10): get_health(), get_system_profile(), chat_with_copilot(), ChatRequest, get_ollama_status(), ask_ollama_copilot(), check_ollama_status(), offline_fallback_copilot() (+2 more)

### Community 3 - "run.py"
Cohesion: 0.09
Nodes (14): get_demo_project(), serve_media_file(), ensure_default_sfx_library(), list_sfx_library(), render_timeline_project(), run_standalone(), do_GET(), do_OPTIONS() (+6 more)

### Community 4 - "verify_system.py"
Cohesion: 0.17
Nodes (15): export_srt(), format_timestamp_srt(), transcribe_audio_file(), log_fail(), log_success(), log_test(), main(), test_1_hardware_profile() (+7 more)

### Community 5 - "realsfx_service.py"
Cohesion: 0.12
Nodes (10): generate_sfx(), SFXGenerateRequest, generate_cinematic_boom(), generate_custom_sfx(), generate_glitch(), generate_laser_zap(), generate_riser(), generate_ui_pop() (+2 more)

### Community 6 - "analyze_audio_track"
Cohesion: 0.12
Nodes (8): analyze_audio(), AnalyzeRequest, compute_ducking(), DuckingRequest, analyze_audio_track(), compute_auto_ducking(), extract_audio_to_wav(), read_wav_samples()

### Community 7 - "super_ai_editor"
Cohesion: 0.10
Nodes (20): context, dockerfile, container_name, image, ports, profiles, restart, volumes (+12 more)

### Community 8 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+9 more)

### Community 9 - "index.ts"
Cohesion: 0.25
Nodes (7): HardwareProfile, MotionSkillItem, RealSFXItem, ThreeJsElement, TimelineAction, VideoClip, WhisperSubtitle

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `render_timeline_project()` connect `run.py` to `main.py`, `test_all_services.py`, `export_video`, `verify_system.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08635703918722787 - nodes in this community are weakly interconnected._
- **Why does `run_standalone()` connect `run.py` to `test_all_services.py`, `verify_system.py`, `realsfx_service.py`, `analyze_audio_track`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.06923076923076923 - nodes in this community are weakly interconnected._
- **Why does `analyze_audio_track()` connect `analyze_audio_track` to `main.py`, `test_all_services.py`, `run.py`, `verify_system.py`, `realsfx_service.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Should `test_all_services.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1006006006006006 - nodes in this community are weakly interconnected._
- **Should `run.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._