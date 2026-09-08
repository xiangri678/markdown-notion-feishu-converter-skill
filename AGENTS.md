# AGENTS.md

This file records project-specific instructions for AI coding agents.

## Project Rules

- Keep every published skill free of personal paths, account identifiers, database IDs, channel IDs, credentials, and private output.
- Preserve third-party attribution and licenses. Do not claim imported or bundled skills as original work.
- Keep `SKILL.md` focused; move conditional procedures to a directly linked file under `references/`.

## Architecture Notes

- Each skill is independently installable from its directory under `skills/`.
- Scripts must resolve sibling resources relative to their own file, never from a specific user's home directory.

## Data and API Contracts

- External writes require user authorization and destination read-back.
- Public web acquisition must not read browser profiles or bypass access controls.

## Validation Commands

- Run the skill-creator `quick_validate.py` against every changed skill.
- Compile changed Python scripts with `python3 -m py_compile`.
- Run script help and non-mutating smoke checks where the host platform supports them.

## Known Pitfalls

- Hermes CLI flags and scheduler behavior vary by release; verify them against the installed version.
- A successful job trigger or HTTP response is not proof that the intended work completed.

## Debugging Playbook

- Inspect the smallest failing stage, then verify the corresponding local artifact and external read-back independently.

## Do Not Change Without Care

- Do not add real credentials, captured cookies, personal database schemas, or private case data to examples or tests.
