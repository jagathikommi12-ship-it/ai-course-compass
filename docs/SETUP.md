# Setup guide

This walks through creating the Supabase project, wiring up secrets, and
running all three pieces locally: the FastAPI backend, the React app, and
the Gradio chat app.

## 1. Create the Supabase project

1. Go to https://supabase.com/dashboard and create a new project (any name,
   e.g. `ai-course-compass`). Pick a strong database password and save it
   somewhere — you won't need it for this app, but Supabase requires one.
2. Wait for provisioning to finish (a couple minutes).
3. In the left sidebar go to **Project Settings > API**. You'll need three
   values from this page throughout setup:
   - **Project URL** (e.g. `https://abcd1234.supabase.co`)
   - **anon public** key
   - **service_role** key (click "Reveal" — treat this like a password,
     never share it or put it in frontend code)
4. Still in Project Settings > API, scroll to **JWT Settings** and copy the
   **JWT Secret** — the backend uses this to verify login tokens without a
   network round trip.

## 2. Run the database migrations

1. In the Supabase dashboard, open the **SQL Editor**.
2. Paste and run `supabase/migrations/0001_init_schema.sql` (creates all
   tables + the auto-profile trigger).
3. Paste and run `supabase/migrations/0002_rls_policies.sql` (locks down
   per-user data with Row Level Security — do not skip this step).
4. Paste and run `supabase/seed/seed_courses.sql` to load the mock CS
   dataset so the app has something to show. Swap this out with real data
   later per `docs/DATA_FORMAT.md`.

(If you'd rather use the Supabase CLI: `supabase link`, then
`supabase db push` picks up everything in `supabase/migrations/`
automatically, and you can run the seed file with
`psql "$DATABASE_URL" -f supabase/seed/seed_courses.sql`.)

## 3. Enable email/password auth

By default Supabase projects already have email/password sign-in enabled
under **Authentication > Providers > Email**. Leave "Confirm email" on if
you want students to verify their address before logging in (recommended
for anything more than a quick demo among friends).

## 4. Get an Anthropic API key

Create one at https://console.anthropic.com/ if you don't have one. This
powers the chat agent's reasoning.

## 5. Configure and run the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: fill in SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
# SUPABASE_JWT_SECRET, ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs to confirm it's up (interactive API docs).

Run the test suite any time you touch the requirement logic:

```bash
python -m pytest
```

## 6. Configure and run the React app

```bash
cd frontend
npm install
cp .env.example .env
# edit .env: fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
# (VITE_API_BASE_URL defaults to http://localhost:8000)
npm run dev
```

Visit http://localhost:5173, sign up with an email/password, and you
should land on the dashboard.

## 7. Configure and run the Gradio app

```bash
cd gradio_app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: fill in SUPABASE_URL, SUPABASE_ANON_KEY
python app.py
```

Visit the local URL it prints (usually http://127.0.0.1:7860) and log in
with the same account you created in the React app — completed courses are
shared, since both apps hit the same backend and database.

## Security notes (what's already handled, and what to keep in mind)

- **RLS is the real enforcement layer.** Every per-user table
  (`user_completed_courses`, `profiles`) only allows a row to be
  read/written by its owner (`auth.uid() = user_id`), and the reference
  catalog tables are read-only to anyone but the service role. This holds
  even if the backend had a bug — Postgres itself refuses the query.
- **The service_role key never leaves the backend.** Only
  `backend/app/supabase_client.py` constructs a client with it. The React
  app and Gradio app only ever hold the anon key, which is safe to ship to
  a browser precisely because RLS constrains what it can do.
- **The backend never trusts a user_id from the request.** Every
  per-user endpoint depends on `get_current_user` (`backend/app/auth.py`),
  which verifies the Supabase JWT's signature locally against
  `SUPABASE_JWT_SECRET` and reads `user_id` out of the verified token —
  never out of a request body or query param.
- **The LLM can't fabricate whether a requirement is satisfied.** The
  Claude agent's tools (`backend/app/agent/tools.py`) call the same
  deterministic `requirement_engine` the REST endpoints use; the model can
  only relay what that engine computed, and is explicitly instructed to
  call `check_course_ambiguity` before confirming a cross-listed course
  counts.
