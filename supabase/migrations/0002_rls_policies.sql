-- Row Level Security policies.
--
-- Threat model: any authenticated student can read the shared catalog, but
-- must never be able to read or write another student's completed-course
-- list, and must never be able to modify the shared catalog/requirements
-- (only the backend, using the service_role key, does that).
--
-- The service_role key bypasses RLS entirely (Supabase default), so it is
-- used only server-side (FastAPI backend) for catalog ingestion/admin
-- writes and NEVER shipped to the React app or Gradio app.

alter table public.courses enable row level security;
alter table public.course_prerequisites enable row level security;
alter table public.degree_programs enable row level security;
alter table public.requirement_categories enable row level security;
alter table public.requirement_courses enable row level security;
alter table public.profiles enable row level security;
alter table public.user_completed_courses enable row level security;

-- ---------------------------------------------------------------------------
-- Reference data: readable by any logged-in user, writable only by service_role
-- (no policy needed to allow service_role — it bypasses RLS — so we only
-- add SELECT policies for the authenticated role here).
-- ---------------------------------------------------------------------------

drop policy if exists "courses_read_authenticated" on public.courses;
create policy "courses_read_authenticated"
  on public.courses for select
  to authenticated
  using (true);

drop policy if exists "course_prereqs_read_authenticated" on public.course_prerequisites;
create policy "course_prereqs_read_authenticated"
  on public.course_prerequisites for select
  to authenticated
  using (true);

drop policy if exists "degree_programs_read_authenticated" on public.degree_programs;
create policy "degree_programs_read_authenticated"
  on public.degree_programs for select
  to authenticated
  using (true);

drop policy if exists "requirement_categories_read_authenticated" on public.requirement_categories;
create policy "requirement_categories_read_authenticated"
  on public.requirement_categories for select
  to authenticated
  using (true);

drop policy if exists "requirement_courses_read_authenticated" on public.requirement_courses;
create policy "requirement_courses_read_authenticated"
  on public.requirement_courses for select
  to authenticated
  using (true);

-- ---------------------------------------------------------------------------
-- Per-user data: strictly owner-only
-- ---------------------------------------------------------------------------

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  to authenticated
  using (auth.uid() = user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- Note: no insert policy for profiles — rows are created only by the
-- handle_new_user() trigger (security definer), never directly by clients.

drop policy if exists "completed_select_own" on public.user_completed_courses;
create policy "completed_select_own"
  on public.user_completed_courses for select
  to authenticated
  using (auth.uid() = user_id);

drop policy if exists "completed_insert_own" on public.user_completed_courses;
create policy "completed_insert_own"
  on public.user_completed_courses for insert
  to authenticated
  with check (auth.uid() = user_id);

drop policy if exists "completed_update_own" on public.user_completed_courses;
create policy "completed_update_own"
  on public.user_completed_courses for update
  to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "completed_delete_own" on public.user_completed_courses;
create policy "completed_delete_own"
  on public.user_completed_courses for delete
  to authenticated
  using (auth.uid() = user_id);

-- No policies at all for the 'anon' role on any table above: unauthenticated
-- requests are rejected by default once RLS is enabled with no matching
-- policy, so the catalog is only visible to signed-in users, and per-user
-- rows are only ever visible to their owner.
