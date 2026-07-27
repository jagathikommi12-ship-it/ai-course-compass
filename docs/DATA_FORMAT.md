# The course data, and how to extend it

`supabase/seed/seed_courses.sql` loads the **real** UMass Amherst BS
Computer Science requirements and course catalog (Fall 2026), built from
the CICS degree requirements page and course descriptions PDF. It covers:

- The intro sequence (CICS 110/160/210), core CS courses, math foundation,
  COMPSCI 311, and the CS elective tiers (300-399, 400+, plus the "1 more
  300+ or approved outside" slot)
- The Integrative Experience (IE) and Junior Year Writing (JYW)
  requirements, including that COMPSCI 320/326 double-count as both a CS
  Elective and the IE requirement
- The Lab Science requirement's approved course list
- A real "looks like it counts but doesn't" case: COMPSCI 590RM is
  explicitly excluded from the CS Elective pool per the catalog, even
  though it has a COMPSCI prefix
- Legacy course-code renames (e.g. CICS 110 was formerly INFO 190S) as
  `notes`, since "this used to be a different code" is exactly the kind of
  thing a friend with an older transcript might trip over

See the header comment in the seed file itself for the specific
simplifications made while transcribing it from the PDF (grad-only courses
omitted, some multi-department OR-prereq chains trimmed to the CS-relevant
paths, a handful of outside-department courses added as lightweight stub
rows since they weren't in the CICS catalog excerpt). It was validated by
running the migrations + seed against a real local Postgres instance
before being committed, but catalogs change term to term — spot-check
anything surprising against SPIRE or an advisor before trusting it for a
real registration decision.

## Extending it (new terms, other majors/minors, corrections)

Any format works — a PDF, a spreadsheet, pasted catalog text. Hand it over
and it'll get converted into the same shape. If you want to write it
yourself, here's the shape to match:

**Courses** — one row per course:
```sql
insert into public.courses (code, title, description, credits, department, cross_listed_as, offered_terms, notes)
values ('COMPSCI 345', 'Practice & Applications of Data Management', '...', 3, 'COMPSCI', '{}', '{Spring}', '');
```
- `cross_listed_as`: other department codes this course is concurrently
  listed under, if any.
- `notes`: freeform — this is where "this course was renamed/cross-listed
  differently" or "doesn't count despite looking like it should" caveats
  go. The agent is instructed to surface whatever's in here before
  confirming a course counts.

**Prerequisites** — one row per (course, individual prereq):
```sql
insert into public.course_prerequisites (course_code, prereq_code, group_id, min_grade)
values ('COMPSCI 311', 'COMPSCI 250', 0, 'C');
```
- Rows sharing the same `group_id` for a course are AND'd together (need
  all of them). Different `group_id`s are alternative paths (need any ONE
  full group) — see COMPSCI 311 in the seed file for a real "(A and B) OR
  (C and D)" example.
- `min_grade` defaults to null (any passing grade); set it when the
  catalog specifies something like "B or better."

**Degree programs + requirement categories**:
```sql
insert into public.degree_programs (name, program_type, description)
values ('BS Computer Science', 'major', '...');

insert into public.requirement_categories (program_id, name, description, min_courses)
values ('<program-id>', 'CS Electives (300-399)', '3 additional electives numbered 300+.', 3);
```
- Use `min_courses` for "complete N of these courses" categories, or
  `min_credits` instead for "earn N credits from this list" categories.

**Which courses satisfy which category** (this is what makes "does X count
toward my major" answerable, including double-counting):
```sql
insert into public.requirement_courses (category_id, course_code, satisfies_note)
values ('<category-id>', 'COMPSCI 320', 'Also satisfies the IE Requirement — same course, not an extra one.');
```
- A course can appear under more than one category — that's intentional
  (see COMPSCI 320/326 in the seed file), and the app flags it as
  "double-counted" so students see it rather than assuming.

## Re-running after edits

The seed file is written with `on conflict ... do update` / `do nothing`,
so re-running it after edits is safe and won't create duplicates. Run it
the same way as initial setup (Supabase SQL Editor, or `psql` via the CLI —
see `docs/SETUP.md` step 2).
