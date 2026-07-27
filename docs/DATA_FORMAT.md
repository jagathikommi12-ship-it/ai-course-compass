# Swapping in real course data

`supabase/seed/seed_courses.sql` currently loads a small **mock** dataset
(generic course codes like `CS 121`, not real UMass courses) just so the
app has something real to check off and query. Replace it with the actual
CS BS requirements + course list whenever you have them.

## What to hand off

You mentioned giving:

1. **The BS in CS degree requirements** — the structured breakdown (core
   courses, theory/systems courses, electives, math foundation, gen-eds,
   how many of each are required).
2. **The full list of courses offered to CS students, with prerequisites**
   — ideally with course codes, titles, short descriptions, and which
   course(s) each one requires.

Any format works — a PDF, a spreadsheet, pasted text from the course
catalog/department site. I'll convert it into the same shape as the seed
file below. If you *do* want to write it yourself (or hand it to a
teammate), here's the shape to match:

## Shape to match (see `supabase/seed/seed_courses.sql` for a full example)

**Courses** — one row per course:
```sql
insert into public.courses (code, title, description, credits, department, cross_listed_as, offered_terms, notes)
values ('CS 187', 'Programming with Data Structures', '...', 4, 'CS', '{}', '{Fall,Spring}', '');
```
- `cross_listed_as`: other department codes this course is also listed
  under (e.g. `{STAT 240}`), if any.
- `notes`: freeform — this is exactly where "this course counts
  differently depending on how it was cross-listed last year" type caveats
  go. The agent is instructed to surface whatever's in here before
  confirming a course counts.

**Prerequisites** — one row per (course, individual prereq):
```sql
insert into public.course_prerequisites (course_code, prereq_code, group_id)
values ('CS 250', 'CS 187', 0);
```
- Rows sharing the same `group_id` for a course are AND'd together (need
  all of them). Different `group_id`s are alternative paths (need any ONE
  full group) — use this for "either (A and B) or just C" prerequisite
  structures, which do show up in real catalogs.

**Degree programs + requirement categories**:
```sql
insert into public.degree_programs (name, program_type, description)
values ('BS Computer Science', 'major', '...');

insert into public.requirement_categories (program_id, name, description, min_courses)
values ('<program-id>', 'CS Electives', 'Choose any 3 upper-level electives.', 3);
```
- Use `min_courses` for "complete N of these courses" categories, or
  `min_credits` instead for "earn N credits from this list" categories.

**Which courses satisfy which category** (this is what makes "does X
count toward my major or minor" answerable, including double-counting):
```sql
insert into public.requirement_courses (category_id, course_code, satisfies_note)
values ('<category-id>', 'CS 345', 'Only counts if taken as INFO 345 — verify with advisor.');
```
- A course can appear under more than one category (major + minor, or two
  elective buckets) — that's intentional, and the app flags it as a
  "double-counted" course so students can see it rather than assuming.
- `satisfies_note` is the per-requirement caveat, distinct from the
  course-level `notes` field, for cases like "this elective satisfies the
  Business minor only for students who declared before Fall 2024."

## Re-running after you provide real data

Once the real data is in a new/updated seed file, run it the same way as
the mock one (Supabase SQL Editor, or `psql` via the CLI — see
`docs/SETUP.md` step 2). It's written with `on conflict ... do update` /
`do nothing`, so re-running it is safe and won't create duplicates.
