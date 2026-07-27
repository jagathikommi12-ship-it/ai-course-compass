-- auth.uid() re-evaluates per row in RLS policies unless wrapped in a
-- subselect, which lets Postgres treat it as a stable initplan value
-- instead of re-invoking it per row. Recreate the owner-only policies with
-- (select auth.uid()) — same access semantics, faster at scale.
--
-- Found by Supabase's built-in performance advisor after applying 0001/0002.

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "completed_select_own" on public.user_completed_courses;
create policy "completed_select_own"
  on public.user_completed_courses for select
  to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "completed_insert_own" on public.user_completed_courses;
create policy "completed_insert_own"
  on public.user_completed_courses for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "completed_update_own" on public.user_completed_courses;
create policy "completed_update_own"
  on public.user_completed_courses for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "completed_delete_own" on public.user_completed_courses;
create policy "completed_delete_own"
  on public.user_completed_courses for delete
  to authenticated
  using ((select auth.uid()) = user_id);

-- Missing covering indexes the advisor flagged on two foreign keys.
create index if not exists idx_profiles_primary_program on public.profiles(primary_program_id);
create index if not exists idx_user_completed_course_code on public.user_completed_courses(course_code);
