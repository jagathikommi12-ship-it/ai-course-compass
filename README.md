# AI Course Compass — Degree Requirement Navigator

Helps students answer "what am I still missing for my major/minor?", "does
this elective count?", and "what am I eligible to take next?" — backed by a
shared course catalog + prerequisite graph, per-student progress tracking,
and a Claude-powered chat agent that reasons over both.

Built for multiple students to use with their own accounts, not tied to any
one person's degree audit.

## Pieces

| Piece | Stack | What it does |
|---|---|---|
| `backend/` | FastAPI + Claude (Anthropic API) | REST API, deterministic requirement-checking logic, Claude agent with tool-calling |
| `frontend/` | Vite + React + TypeScript + Tailwind | Interactive prerequisite drill-down, requirement checklist, Recommendation Mode, chat |
| `gradio_app/` | Gradio | Conversational-only interface, same login and same backend as the React app |
| `supabase/` | SQL migrations + seed | Schema, Row Level Security policies, mock CS dataset |

Both frontends authenticate against the same Supabase project, so a
student's completed courses and chat answers are consistent whichever one
they use.

## Getting started

See `docs/SETUP.md` for the full walkthrough: creating the Supabase
project, running migrations, and starting all three services locally.

## Using real course data

The repo ships with a small mock CS dataset so everything runs end-to-end
out of the box. See `docs/DATA_FORMAT.md` for how to swap in the real BS
CS requirements and course catalog.

## Tests

```bash
cd backend && source .venv/bin/activate && python -m pytest
```

Covers the deterministic requirement engine (`app/services/requirement_engine.py`)
— prerequisite AND/OR logic, category satisfaction by course count or
credits, double-counted courses, and cross-listing ambiguity flagging.
