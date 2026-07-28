-- Semester planner: 4-year/8-semester drag-and-drop plan, credit tracking.
--
-- Model:
--   user_plan_settings — one row per user: incoming transfer/AP/IB credits,
--     and how many REGULAR (Fall/Spring) semesters they're targeting.
--   user_terms — the ordered sequence of term slots in a user's plan.
--     Regular Fall/Spring terms are generated from plan_settings;
--     summer/winter terms can be inserted anywhere by the user. Ordering is
--     via `position` (dense integers, re-sequenced on insert/delete).
--   user_planned_courses — supersedes user_completed_courses with a richer
--     model: a course can be unscheduled (term_id null, just checked off in
--     the list), scheduled into a term, and/or locked (done or certain-
--     enrolled, so it can't be dragged around or blocked by prereq checks
--     the way a tentative future course can).

create table if not exists public.user_plan_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  incoming_credits numeric(5,1) not null default 0,
  target_semesters int not null default 8 check (target_semesters between 1 and 12),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_terms (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  term_type text not null check (term_type in ('fall', 'spring', 'summer', 'winter')),
  label text not null,                 -- e.g. 'Year 1 - Fall', 'Summer after Year 2'
  position int not null,               -- dense ordering across the whole plan
  created_at timestamptz not null default now(),
  unique (user_id, position)
);

create index if not exists idx_user_terms_user on public.user_terms(user_id);

create table if not exists public.user_planned_courses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_code text not null references public.courses(code) on delete cascade,
  term_id uuid references public.user_terms(id) on delete set null,
  status text not null default 'planned' check (status in ('planned', 'completed')),
  locked boolean not null default false,  -- done, or certain (currently enrolled) — can't be dragged/removed casually
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, course_code)
);

create index if not exists idx_user_planned_user on public.user_planned_courses(user_id);
create index if not exists idx_user_planned_term on public.user_planned_courses(term_id);

-- Carry over anything already tracked in the older, simpler completed-courses
-- table so nobody's existing checked-off progress disappears.
insert into public.user_planned_courses (user_id, course_code, term_id, status, locked)
select user_id, course_code, null, 'completed', true
from public.user_completed_courses
on conflict (user_id, course_code) do nothing;

-- How many total credits the degree requires, for the "how many more do I
-- need" tracker. A simple flat number rather than trying to derive it from
-- category minimums, since real degree audits quote this as a single figure.
alter table public.degree_programs
  add column if not exists total_credits_required numeric(6,1) not null default 120;

alter table public.user_plan_settings enable row level security;
alter table public.user_terms enable row level security;
alter table public.user_planned_courses enable row level security;

drop policy if exists "plan_settings_own" on public.user_plan_settings;
create policy "plan_settings_own"
  on public.user_plan_settings for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "user_terms_own" on public.user_terms;
create policy "user_terms_own"
  on public.user_terms for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "user_planned_courses_own" on public.user_planned_courses;
create policy "user_planned_courses_own"
  on public.user_planned_courses for all
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
