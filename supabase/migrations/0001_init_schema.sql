-- AI Course Compass — core schema
-- Public reference data (courses, requirements) is readable by any authenticated
-- user but only writable by the service role (backend). Per-user data
-- (completed courses) is private to its owner via RLS in 0002_rls_policies.sql.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Reference data: courses, prerequisites, degree requirements
-- ---------------------------------------------------------------------------

create table if not exists public.courses (
  code text primary key,                    -- e.g. 'COMPSCI 187'
  title text not null,
  description text not null default '',
  credits numeric(4,1) not null default 3,
  department text not null default 'COMPSCI',
  cross_listed_as text[] not null default '{}',  -- e.g. {'STATS 240'}
  offered_terms text[] not null default '{}',    -- e.g. {'Fall','Spring'}
  notes text not null default '',           -- freeform: "counts toward X only if taken before Y", cross-listing caveats, etc.
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.courses is 'University course catalog, shared reference data.';

-- Prerequisite edges. A course may need ALL of a group, or ANY ONE of a group
-- (group_id lets us express "(A AND B) OR C" style prereqs).
create table if not exists public.course_prerequisites (
  id uuid primary key default gen_random_uuid(),
  course_code text not null references public.courses(code) on delete cascade,
  prereq_code text not null references public.courses(code) on delete cascade,
  group_id int not null default 0,          -- prereqs sharing a group_id are AND'd together; different group_ids are OR'd
  min_grade text,                            -- e.g. 'C' if a minimum grade is required
  created_at timestamptz not null default now(),
  unique (course_code, prereq_code, group_id)
);

create index if not exists idx_course_prereqs_course on public.course_prerequisites(course_code);
create index if not exists idx_course_prereqs_prereq on public.course_prerequisites(prereq_code);

-- Degree programs (e.g. "BS Computer Science", "Business Minor")
create table if not exists public.degree_programs (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,                -- 'BS Computer Science'
  program_type text not null default 'major', -- 'major' | 'minor' | 'gen_ed'
  description text not null default '',
  created_at timestamptz not null default now()
);

-- Requirement categories within a program (e.g. "CS Core", "CS Electives", "Math Foundation")
create table if not exists public.requirement_categories (
  id uuid primary key default gen_random_uuid(),
  program_id uuid not null references public.degree_programs(id) on delete cascade,
  name text not null,                       -- 'CS Core Courses'
  description text not null default '',
  min_courses int,                          -- e.g. must complete 5 of the listed courses
  min_credits numeric(5,1),                 -- alternative/additional threshold, e.g. 12 credits
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  unique (program_id, name)
);

-- Which courses count toward which requirement category. A course can satisfy
-- more than one category (this is exactly the "does X count twice" question),
-- and satisfies_note captures caveats like "only if taken as COMPSCI, not the
-- cross-listed STATS section".
create table if not exists public.requirement_courses (
  id uuid primary key default gen_random_uuid(),
  category_id uuid not null references public.requirement_categories(id) on delete cascade,
  course_code text not null references public.courses(code) on delete cascade,
  satisfies_note text not null default '',
  created_at timestamptz not null default now(),
  unique (category_id, course_code)
);

create index if not exists idx_requirement_courses_category on public.requirement_courses(category_id);
create index if not exists idx_requirement_courses_course on public.requirement_courses(course_code);

-- ---------------------------------------------------------------------------
-- Per-user data
-- ---------------------------------------------------------------------------

-- Thin profile row, one per auth user. Created automatically by trigger below.
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  primary_program_id uuid references public.degree_programs(id),
  created_at timestamptz not null default now()
);

create table if not exists public.user_completed_courses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_code text not null references public.courses(code) on delete cascade,
  term text,                                -- e.g. 'Fall 2025', optional/freeform
  grade text,
  created_at timestamptz not null default now(),
  unique (user_id, course_code)
);

create index if not exists idx_user_completed_user on public.user_completed_courses(user_id);

-- Auto-create a profile row whenever a new auth user signs up.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (user_id, display_name)
  values (new.id, new.raw_user_meta_data ->> 'display_name');
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
