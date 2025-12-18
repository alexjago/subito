# Repository Guidelines

## Project Structure & Module Organisation
- `Subito.py` holds the core CLI workflow for converting MuseScore or MIDI sources into individual practice tracks.
- `config.ini` stores part layouts, volume defaults, and layout priorities; keep local overrides out of version control.
- `Snippets.md` and `thoughts.txt` capture reference material and future ideas; sync any actionable items into issues.
- Outputs are written beside the source path you invoke; prefer staging them in a dedicated `output/` folder when sharing results.

## Task Tracking

Use 'bd' for task tracking. 

## Build, Test, and Development Commands
- `python3 Subito.py --help` lists supported flags and expected inputs.
- `python3 Subito.py path/to/source.mid ./output` runs the default MIDI-to-MIDI workflow.
- `python3 Subito.py --musescore --mp3 scores/ ./output` performs MuseScore-to-MP3 conversions (requires MuseScore CLI plus `midicsv`/`csvmidi` binaries on `PATH`).
- `python3 Subito.py --verbose …` surfaces parsing details; capture logs for bug reports.

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, lowercase `snake_case` for functions/variables, and ALL_CAPS for module-level constants (e.g. `CONFIGPATH`).
- Keep CLI flags lowercase with single dashes to mirror existing arguments.
- Prefer standard-library solutions; document any new external dependency in `README.md`.

## Testing Guidelines
- No automated test suite exists; validate changes by running representative conversions covering MuseScore and MIDI inputs.
- Record expected artefacts (MIDI/MP3 counts, volume emphasis) and compare before/after results; flag regressions in PRs.
- Use `--filter` to narrow to deterministic fixtures when debugging.

## Commit & Pull Request Guidelines
- Match the current Git history: short, present-tense summaries in lowercase (e.g. `add layout validation`).
- Reference issues or link to reproduction assets when relevant.
- For pull requests, include: goal summary, key command(s) used for verification, notable config changes, and sample output paths or screenshots when audio isn’t practical.

## Configuration & Environment Tips
- Keep `config.ini` minimal; place experimental layouts in a separate file and pass it via `--config`.
- On macOS/Linux, add MuseScore’s CLI (`mscore`/`mscore3`) and `midicsv` tools to your shell `PATH` before running conversions.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
