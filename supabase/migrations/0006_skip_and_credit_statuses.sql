-- Lets a course be marked 'skipped' (tested out of it, no credit) or
-- 'credited' (AP/IB/transfer credit received) instead of only
-- 'planned'/'completed'. Both statuses satisfy prerequisites for later
-- courses without ever being scheduled into a term; the app enforces
-- term_id staying null for them (see app/routers/plan.py).

alter table public.user_planned_courses
  drop constraint if exists user_planned_courses_status_check;

alter table public.user_planned_courses
  add constraint user_planned_courses_status_check
  check (status in ('planned', 'completed', 'skipped', 'credited'));
