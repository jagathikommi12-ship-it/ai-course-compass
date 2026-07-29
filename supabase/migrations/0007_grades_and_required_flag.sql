-- Two real gaps found by spot-checking against the seeded UMass data:
--
-- 1. course_prerequisites.min_grade has existed since the very first seed
--    (e.g. COMPSCI 514 needs a B+ in COMPSCI 240/311, COMPSCI 575 needs a B)
--    but nothing in the app ever read it — prereq checks only looked at
--    whether the course was done at all, never the grade. Fixing that needs
--    to know what grade the student actually got, which we never stored.
--
-- 2. requirement_courses had no way to say "this specific course in the
--    category is optional" — mandatory-vs-choice was guessed from category
--    totals, which breaks for a category that's MOSTLY required with one
--    either/or slot (Math Foundation: MATH 131/132/235 are all required,
--    but the 4th slot is MATH 233 OR STATISTC 315 — picking either is fine).

alter table public.user_planned_courses
  add column if not exists grade text
  check (grade is null or grade in ('A','A-','B+','B','B-','C+','C','C-','D+','D','D-','F'));

alter table public.requirement_courses
  add column if not exists is_required boolean not null default true;

-- The only currently-known "mixed" category: Math Foundation's 4th slot is
-- a real either/or between these two, everything else in that category is
-- unconditionally required.
update public.requirement_courses rc
set is_required = false
from public.requirement_categories cat
where rc.category_id = cat.id
  and cat.name = 'Mathematics Foundation'
  and rc.course_code in ('MATH 233', 'STATISTC 315');
