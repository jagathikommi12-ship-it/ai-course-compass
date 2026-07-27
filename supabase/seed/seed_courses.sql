-- MOCK data for local development / demoing the app end-to-end.
-- Course codes, descriptions, and prereq chains here are illustrative
-- placeholders, NOT the real UMass catalog. Replace via docs/DATA_FORMAT.md
-- once real CS BS requirements + course list are available.
--
-- This seed deliberately includes two tricky cases the agent is supposed to
-- reason about:
--   1. CS 311 (Algorithms) can be reached via two different prereq paths
--      (an AND group vs an alternate AND group) — tests OR-of-AND-groups logic.
--   2. CS 345 is cross-listed as INFO 345 and counts toward the Business
--      Minor only under specific conditions — tests the "conflict flagging"
--      requirement (courses that may or may not count depending on how they
--      were taken).

begin;

-- ---------------------------------------------------------------------------
-- Courses
-- ---------------------------------------------------------------------------
insert into public.courses (code, title, description, credits, department, cross_listed_as, offered_terms, notes) values
  ('CS 121', 'Introduction to Problem Solving with Computers', 'Intro programming course, no prior experience assumed.', 4, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 187', 'Programming with Data Structures', 'Data structures, recursion, algorithm analysis basics.', 4, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 220', 'Programming Languages', 'Functional and logic programming paradigms.', 3, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 230', 'Computer Systems Principles', 'Assembly, memory hierarchy, C programming.', 4, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 240', 'Reasoning Under Uncertainty', 'Probability for computer scientists.', 3, 'CS', '{STAT 240}', '{Fall,Spring}', 'Cross-listed with STAT 240; confirm with advisor which section you were enrolled in counts for your program.'),
  ('CS 250', 'Introduction to Computation Theory', 'Automata, computability, complexity.', 3, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 311', 'Algorithms', 'Design and analysis of algorithms.', 3, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 320', 'Software Engineering', 'Team-based software development practices.', 3, 'CS', '{}', '{Fall}', ''),
  ('CS 345', 'Information Systems', 'Databases and information systems for business contexts.', 3, 'CS', '{INFO 345}', '{Spring}', 'Cross-listed as INFO 345. Counts toward the Business Minor ONLY when taken under the INFO 345 listing per last year''s catalog change — verify with the Business department before assuming it counts.'),
  ('CS 350', 'Operating Systems', 'Processes, concurrency, memory management.', 3, 'CS', '{}', '{Fall,Spring}', ''),
  ('CS 425', 'Computer Networks', 'Network protocols and distributed systems basics.', 3, 'CS', '{}', '{Fall}', ''),
  ('CS 445', 'Database Systems', 'Relational databases, SQL, transactions.', 3, 'CS', '{INFO 445}', '{Spring}', 'Cross-listed as INFO 445.'),
  ('CS 460', 'Introduction to Artificial Intelligence', 'Search, knowledge representation, intro ML.', 3, 'CS', '{}', '{Fall}', ''),
  ('MATH 131', 'Calculus I', 'Single-variable differential calculus.', 4, 'MATH', '{}', '{Fall,Spring}', ''),
  ('MATH 132', 'Calculus II', 'Single-variable integral calculus and series.', 4, 'MATH', '{}', '{Fall,Spring}', ''),
  ('MATH 235', 'Introduction to Linear Algebra', 'Vector spaces, matrices, eigenvalues.', 3, 'MATH', '{}', '{Fall,Spring}', ''),
  ('ENGL 112', 'College Writing', 'Written communication gen-ed requirement.', 3, 'ENGL', '{}', '{Fall,Spring}', ''),
  ('PHYS 151', 'Physics I', 'Mechanics; satisfies natural science gen-ed.', 4, 'PHYS', '{}', '{Fall,Spring}', ''),
  ('BUS 101', 'Introduction to Business', 'Overview of business fundamentals.', 3, 'BUS', '{}', '{Fall,Spring}', ''),
  ('BUS 210', 'Financial Accounting', 'Core accounting principles.', 3, 'BUS', '{}', '{Fall,Spring}', ''),
  ('BUS 301', 'Marketing Principles', 'Core marketing concepts.', 3, 'BUS', '{}', '{Fall}', '')
on conflict (code) do update set
  title = excluded.title,
  description = excluded.description,
  credits = excluded.credits,
  department = excluded.department,
  cross_listed_as = excluded.cross_listed_as,
  offered_terms = excluded.offered_terms,
  notes = excluded.notes;

-- ---------------------------------------------------------------------------
-- Prerequisites
-- (group_id: rows sharing a group_id for the same course_code are AND'd;
--  different group_ids are alternative (OR'd) paths.)
-- ---------------------------------------------------------------------------
insert into public.course_prerequisites (course_code, prereq_code, group_id) values
  ('CS 187', 'CS 121', 0),
  ('CS 220', 'CS 187', 0),
  ('CS 230', 'CS 187', 0),
  ('CS 240', 'MATH 132', 0),
  ('CS 250', 'CS 187', 0),
  ('CS 250', 'MATH 235', 0),
  -- CS 311 reachable via (CS 230 AND CS 250) [group 0] OR (CS 220) alone [group 1]
  ('CS 311', 'CS 230', 0),
  ('CS 311', 'CS 250', 0),
  ('CS 311', 'CS 220', 1),
  ('CS 320', 'CS 230', 0),
  ('CS 345', 'CS 187', 0),
  ('CS 350', 'CS 230', 0),
  ('CS 425', 'CS 350', 0),
  ('CS 445', 'CS 220', 0),
  ('CS 460', 'CS 240', 0),
  ('CS 460', 'CS 311', 0),
  ('MATH 132', 'MATH 131', 0),
  ('MATH 235', 'MATH 131', 0),
  ('BUS 210', 'BUS 101', 0),
  ('BUS 301', 'BUS 210', 0)
on conflict (course_code, prereq_code, group_id) do nothing;

-- ---------------------------------------------------------------------------
-- Degree programs + requirement categories
-- ---------------------------------------------------------------------------
insert into public.degree_programs (name, program_type, description) values
  ('BS Computer Science', 'major', 'Mock BS in Computer Science requirements.'),
  ('Business Minor', 'minor', 'Mock Business minor requirements.')
on conflict (name) do nothing;

with cs as (select id from public.degree_programs where name = 'BS Computer Science'),
     bm as (select id from public.degree_programs where name = 'Business Minor')
insert into public.requirement_categories (program_id, name, description, min_courses, sort_order)
select cs.id, v.name, v.description, v.min_courses, v.sort_order
from cs, (values
  ('CS Foundation', 'Intro programming + data structures + systems.', 3, 0),
  ('CS Theory & Systems Core', 'Languages, theory, and algorithms core.', 3, 1),
  ('CS Electives', 'Choose any 3 upper-level CS electives.', 3, 2),
  ('Math Foundation', 'Calculus sequence and linear algebra.', 3, 3),
  ('Gen Ed - Written Communication', 'College writing requirement.', 1, 4),
  ('Gen Ed - Natural Science', 'Lab science requirement.', 1, 5)
) as v(name, description, min_courses, sort_order)
union all
select bm.id, v.name, v.description, v.min_courses, v.sort_order
from bm, (values
  ('Business Minor Core', 'Required core business courses.', 3, 0),
  ('Business Minor Electives', 'One additional approved business-adjacent elective.', 1, 1)
) as v(name, description, min_courses, sort_order)
on conflict (program_id, name) do nothing;

-- Map courses to requirement categories
insert into public.requirement_courses (category_id, course_code, satisfies_note)
select rc.id, v.course_code, v.note
from public.requirement_categories rc
join public.degree_programs dp on dp.id = rc.program_id
join (values
  ('BS Computer Science', 'CS Foundation', 'CS 121', ''),
  ('BS Computer Science', 'CS Foundation', 'CS 187', ''),
  ('BS Computer Science', 'CS Foundation', 'CS 230', ''),
  ('BS Computer Science', 'CS Theory & Systems Core', 'CS 220', ''),
  ('BS Computer Science', 'CS Theory & Systems Core', 'CS 250', ''),
  ('BS Computer Science', 'CS Theory & Systems Core', 'CS 311', ''),
  ('BS Computer Science', 'CS Electives', 'CS 320', ''),
  ('BS Computer Science', 'CS Electives', 'CS 345', ''),
  ('BS Computer Science', 'CS Electives', 'CS 350', ''),
  ('BS Computer Science', 'CS Electives', 'CS 425', ''),
  ('BS Computer Science', 'CS Electives', 'CS 445', ''),
  ('BS Computer Science', 'CS Electives', 'CS 460', ''),
  ('BS Computer Science', 'Math Foundation', 'MATH 131', ''),
  ('BS Computer Science', 'Math Foundation', 'MATH 132', ''),
  ('BS Computer Science', 'Math Foundation', 'MATH 235', ''),
  ('BS Computer Science', 'Gen Ed - Written Communication', 'ENGL 112', ''),
  ('BS Computer Science', 'Gen Ed - Natural Science', 'PHYS 151', ''),
  ('Business Minor', 'Business Minor Core', 'BUS 101', ''),
  ('Business Minor', 'Business Minor Core', 'BUS 210', ''),
  ('Business Minor', 'Business Minor Core', 'BUS 301', ''),
  ('Business Minor', 'Business Minor Electives', 'CS 345', 'Only counts if taken/recorded as INFO 345 per current Business dept policy — flagged as a conflict case.')
) as v(program_name, category_name, course_code, note)
  on dp.name = v.program_name and rc.name = v.category_name
on conflict (category_id, course_code) do nothing;

commit;
