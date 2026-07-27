-- REAL UMass Amherst BS Computer Science data, built from:
--   1. The department's "Degree Requirements" page (structure of what's required)
--   2. The CICS Fall 2026 Course Descriptions catalog (course-level prereqs/credits)
--
-- Simplifications made while transcribing (documented here, not silently):
--   - Grad-only courses (600+ and most honors colloquia/seminars) are omitted —
--     they don't count toward undergrad BS-CS electives.
--   - Some prerequisite OR-chains that pull in courses from unrelated
--     departments (e.g. COMPSCI 389's STATISTC/PSYCH/OIM/SOCIOL alternates)
--     are trimmed to the 1-2 most CS-relevant paths; the full alternate list
--     lives in the course's `notes` field so nothing is silently dropped.
--   - Courses outside the CICS catalog (lab sciences, the "outside elective"
--     list, legacy/alternate prereq codes like COMPSCI 187) are included as
--     lightweight stub rows using the titles/credits given in the
--     requirements doc itself, flagged in `notes` as not fully detailed here.
--   - "Counts as a CS Elective" is assumed by default for any COMPSCI course
--     open to CS majors, UNLESS the catalog explicitly says otherwise —
--     COMPSCI 590RM is the one explicit real-world exception, which is
--     exactly the kind of gotcha this app exists to catch.
--
-- This was extracted from a PDF catalog export and should be spot-checked
-- against SPIRE / your Academic Requirements Report before relying on it —
-- catalogs change term to term.

begin;

-- ---------------------------------------------------------------------------
-- Courses
-- ---------------------------------------------------------------------------
insert into public.courses (code, title, description, credits, department, cross_listed_as, offered_terms, notes) values
  ('CICS 110', 'Foundations of Programming', 'Intro to computer programming and problem solving; no prior experience required.', 4, 'CICS', '{}', '{Fall,Spring}', 'Gen Ed R2. Formerly listed under the course code INFO 190S in older records/transcripts.'),
  ('CICS 160', 'Object-Oriented Programming', 'OOP techniques and an introduction to data structures, beyond the CICS 110 level.', 4, 'CICS', '{}', '{Fall,Spring}', 'Gen Ed R2. Formerly listed under the course code INFO 190T in older records/transcripts.'),
  ('CICS 210', 'Data Structures', 'Design, analysis, and implementation of data structures: trees, hash tables, graphs, and more.', 4, 'CICS', '{}', '{Fall,Spring}', 'Gen Ed R2.'),
  ('CICS 256', 'Make: Physical Computing', 'Hands-on physical computing: electronics, microcontroller programming, 3D printing/laser cutting.', 4, 'CICS', '{}', '{Fall,Spring}', 'Satisfies the CS Lab Science Requirement. Currently open to Freshman/Sophomore BS-CS majors only (juniors considered if seats available); not listed as an option on the standard ARR, but an ARR exception is applied automatically near graduation.'),
  ('CICS 305', 'Social Issues in Computing', 'Satisfies the Junior Year Writing (JYW) requirement via technical/science writing about computing and society.', 3, 'CICS', '{}', '{Fall,Spring}', 'CICS Primary Majors only. Double majors for whom CS is the SECONDARY major may use their primary major''s JYW course instead of CICS 305.'),
  ('COMPSCI 198C', 'Intro to the C Programming Language (practicum)', 'Basic C data types, pointers, linked lists, gcc/make tooling.', 1, 'COMPSCI', '{}', '{Fall,Spring}', 'Required prerequisite for COMPSCI 230, effective Fall 2023 — easy to miss since it is a 1-credit practicum, not a normal lecture course.'),
  ('COMPSCI 220', 'Programming Methodology', 'Design strategies and patterns, functional and object-oriented approaches, testing, code refactoring.', 4, 'COMPSCI', '{}', '{Fall,Spring}', ''),
  ('COMPSCI 230', 'Computer Systems Principles', 'C data representation, computer architecture, assembly languages, OS services (I/O, process, synchronization).', 4, 'COMPSCI', '{}', '{Fall,Spring}', ''),
  ('COMPSCI 240', 'Reasoning Under Uncertainty', 'Probability, counting, Bayesian/Markov reasoning, intro statistical estimation.', 4, 'COMPSCI', '{}', '{Fall,Spring}', ''),
  ('COMPSCI 250', 'Introduction to Computation', 'Discrete math, induction/recursion, automata, finite-state machines, regular languages.', 4, 'COMPSCI', '{}', '{Fall,Spring}', 'Required for the CS Major (BS); counts as a CS Elective for the CS Major (BA) instead.'),
  ('COMPSCI 311', 'Introduction to Algorithms', 'Divide-and-conquer, greedy, dynamic programming, network flow, NP-completeness.', 4, 'COMPSCI', '{}', '{Fall,Spring}', 'Required for the CS Major (BS).'),
  ('COMPSCI 320', 'Software Engineering', 'Team-based, full-lifecycle semester-long software development project.', 4, 'COMPSCI', '{}', '{Fall}', 'Satisfies the university Integrative Experience (IE) Requirement AND counts as a CS Elective — it is the SAME course credit satisfying both, not two separate courses. COMPSCI 326 also satisfies IE.'),
  ('COMPSCI 325', 'Intro to Human-Computer Interaction', 'HCI design thinking, evaluation methodologies, human cognition and perception.', 3, 'COMPSCI', '{}', '{Fall}', 'Open to juniors/seniors in CS or Informatics.'),
  ('COMPSCI 326', 'Web Programming', 'Client- and server-side web tech: HTTP, HTML5, CSS, JavaScript, AJAX, SQL, web security.', 4, 'COMPSCI', '{}', '{Spring}', 'Satisfies the university Integrative Experience (IE) Requirement AND counts as a CS Elective — same double-duty caveat as COMPSCI 320.'),
  ('COMPSCI 328', 'Mobile Health Sensing & Analytics', 'Mobile/wearable sensing, signal processing, and ML applied to health and behavior data.', 3, 'COMPSCI', '{}', '{Fall}', ''),
  ('COMPSCI 335', 'Inside the Box: How Computers Work', 'Logic circuits, embedded ARM programming, caches/pipelines/branch predictors.', 3, 'COMPSCI', '{}', '{Fall}', 'Open to senior and junior CS majors only.'),
  ('COMPSCI 345', 'Practice & Applications of Data Management', 'Relational databases, SQL, schema design, transactions, database security.', 3, 'COMPSCI', '{}', '{Spring}', 'Students who already completed COMPSCI 445 need instructor permission to also take this.'),
  ('COMPSCI 360', 'Intro to Computer & Network Security', 'Ciphers, key exchange, web/mobile/AI security, prompt injection and jailbreaking, countermeasures.', 3, 'COMPSCI', '{}', '{Fall,Spring}', ''),
  ('COMPSCI 363', 'Computer Crime Law', 'Legal issues in computer/network crime: authorization, search/seizure, wiretaps, FISA.', 3, 'COMPSCI', '{}', '{Fall}', 'Open to senior/junior CS majors only.'),
  ('COMPSCI 367', 'Reverse Engineering & Exploit Development', 'Intel assembly, vulnerability analysis, Linux binary exploitation, defensive mitigations (ASLR/NX/cookies).', 3, 'COMPSCI', '{}', '{Fall}', 'Counts as a CS Elective, but explicitly does NOT count as an INFORM elective.'),
  ('COMPSCI 377', 'Operating Systems', 'Process/memory management, file systems, distributed systems support.', 4, 'COMPSCI', '{}', '{Fall,Spring}', ''),
  ('COMPSCI 383', 'Artificial Intelligence', 'Overview of industry AI topics with emphasis on machine learning fundamentals.', 3, 'COMPSCI', '{}', '{Fall,Spring}', 'Elective for CS and INFORM Majors.'),
  ('COMPSCI 389', 'Intro to Machine Learning', 'Supervised learning, reinforcement learning, and real-world ML ethics/safety/fairness.', 3, 'COMPSCI', '{}', '{Fall,Spring}', 'Elective for CS and INFORM Majors. Full prereq allows COMPSCI 240 OR STATISTC 315/240/PSYCH 240/OIM 240/RES-ECON 212/SOCIOL 212 — only the CS-relevant paths are modeled here. Take COMPSCI 589 instead if you already have ML experience.'),
  ('COMPSCI 420', 'Software Entrepreneurship', 'Challenge-based learning building early-stage software products with societal benefit.', 3, 'COMPSCI', '{}', '{Spring}', 'Elective for CS and INFORM Majors.'),
  ('COMPSCI 429', 'Software Engineering Project Management', 'Serve as a technical project manager for a COMPSCI 320 team.', 3, 'COMPSCI', '{}', '{Fall}', 'Enrollment by instructor permission only; requires a B or better in a prior COMPSCI 320.'),
  ('COMPSCI 445', 'Information Systems', 'Large-scale data management: relational + semi-structured data, MapReduce/Spark.', 3, 'COMPSCI', '{}', '{Fall}', ''),
  ('COMPSCI 453', 'Computer Networks', 'TCP/IP protocol suite, routing, wireless networks, network security and management.', 3, 'COMPSCI', '{}', '{Fall}', ''),
  ('COMPSCI 461', 'Secure Distributed Systems', 'Byzantine fault tolerance, consensus, blockchain/cryptocurrency security.', 3, 'COMPSCI', '{}', '{Spring}', 'Open to CS majors only. Also usable as an "Any 2" menu choice for the former Security & Privacy track.'),
  ('COMPSCI 485', 'Applications of NLP', 'Text classification, sentiment analysis, machine translation, NLP tooling.', 3, 'COMPSCI', '{}', '{Fall}', ''),
  ('COMPSCI 491P', 'Seminar: Philosophy of AI & Consciousness', 'Dualist vs. monist philosophy of mind applied to Turing-equivalent computing.', 3, 'COMPSCI', '{}', '{Fall}', 'Discussion/reading seminar, no exams.'),
  ('COMPSCI 514', 'Algorithms for Data Science', 'Sampling, sketching, and distributed processing of massive datasets/graphs/streams.', 3, 'COMPSCI', '{}', '{Fall}', ''),
  ('COMPSCI 515', 'Computational Social Choice', 'Game theory (Nash equilibria), matching algorithms, mechanism design.', 3, 'COMPSCI', '{}', '{Spring}', 'Open to junior/senior CS students.'),
  ('COMPSCI 520', 'Theory & Practice of Software Engineering', 'AI for software engineering (automated testing/repair) and software engineering for AI (fairness bugs).', 3, 'COMPSCI', '{}', '{Spring}', ''),
  ('COMPSCI 532', 'Systems for Data Science', 'Scaling parallelism up/out for large-scale data analysis (MapReduce-Hadoop, Spark).', 3, 'COMPSCI', '{}', '{Fall}', 'Counts as a CS Elective for the CS Major.'),
  ('COMPSCI 550', 'Introduction to Simulation', 'Stochastic system simulation for design/evaluation of complex systems.', 3, 'COMPSCI', '{}', '{Fall}', 'Counts as an Elective toward the CS Major.'),
  ('COMPSCI 565', 'Advanced Digital Forensic Systems', 'File carving, filesystem/network/mobile/memory forensics, anti-forensics.', 3, 'COMPSCI', '{}', '{Spring}', ''),
  ('COMPSCI 571', 'Data Visualization & Exploration', 'Perception/design theory, clustering, dimensionality reduction; D3/Python visualization.', 3, 'COMPSCI', '{}', '{Fall}', 'Elective toward CS and INFORM Majors.'),
  ('COMPSCI 575', 'Combinatorics & Graph Theory', 'Graph theory, Euler/Hamiltonian circuits, coloring, matching, generating functions.', 3, 'COMPSCI', '{}', '{Spring}', 'Open to juniors/seniors. Elective toward the CS Major.'),
  ('COMPSCI 589', 'Machine Learning', 'Core ML models: classification, regression, clustering, dimensionality reduction; strong math emphasis.', 3, 'COMPSCI', '{}', '{Fall}', 'MATH 545 requirement is waivable via MATH 235 + MATH 233 (both B+); STATISTC 315/515 is waivable via COMPSCI 240 (B+). Check with your advisor about waivers.'),
  ('COMPSCI 590AF', 'Reverse Engineering & Exploit Development', 'Intel assembly, reverse engineering, Linux binary exploitation, defensive mitigations.', 3, 'COMPSCI', '{}', '{Spring}', ''),
  ('COMPSCI 590OP', 'Applied Numerical Optimization', 'Optimization basics: gradient descent, Newton/quasi-Newton, linear programming, applications.', 3, 'COMPSCI', '{}', '{Spring}', 'Counts as a CS Elective (BS or BA). No formal course prerequisite, but assumes Python, probability/stats, and linear algebra background.'),
  ('COMPSCI 590Q', 'Quantum Information Systems', 'Quantum computing concepts: entanglement, teleportation, Grover''s and Shor''s algorithms.', 3, 'COMPSCI', '{}', '{Fall}', 'Counts as a CS Elective (BA or BS).'),
  ('COMPSCI 590RM', 'Research Methods in Empirical Computer Science', 'Reading/evaluating technical papers; semester-long replication research project.', 3, 'COMPSCI', '{}', '{Fall}', 'Does NOT count as a CS Elective for the CS major (BA or BS), despite the COMPSCI prefix. It only satisfies the 499Y Honors thesis requirement for eligible students. This is exactly the kind of course that looks like it should count but does not.'),
  -- Math foundation
  ('MATH 131', 'Calculus I', 'Single-variable differential calculus.', 4, 'MATH', '{}', '{Fall,Spring}', ''),
  ('MATH 132', 'Calculus II', 'Single-variable integral calculus and series.', 4, 'MATH', '{}', '{Fall,Spring}', ''),
  ('MATH 233', 'Multivariate Calculus', 'Calculus in several variables.', 4, 'MATH', '{}', '{Fall,Spring}', 'Alternative to STATISTC 315 for the 4th math-foundation slot.'),
  ('MATH 235', 'Introduction to Linear Algebra', 'Vector spaces, matrices, eigenvalues.', 4, 'MATH', '{}', '{Fall,Spring}', ''),
  ('STATISTC 315', 'Statistics I', 'Introductory statistics.', 4, 'STATISTC', '{}', '{Fall,Spring}', 'Does NOT replace MATH 132 in the math foundation requirement, even though it (or MATH 233) can fill the 4th math-foundation slot.'),
  -- Approved "outside elective" list (titles/credits per the requirements doc; not in the CICS catalog excerpt)
  ('ECE 353', 'Computer Systems Lab I', 'Approved outside elective for the CS Major.', 4, 'ECE', '{}', '{}', 'Not detailed in the CICS catalog excerpt (credit count approximate) — verify prereqs directly with the ECE department.'),
  ('ECE 547', 'Security Engineering', 'Approved outside elective for the CS Major.', 3, 'ECE', '{}', '{}', 'Formerly ECE 597AB. Not detailed in the CICS catalog excerpt — verify prereqs directly with the ECE department.'),
  ('ECE 668', 'Computer Architecture', 'Approved outside elective for the CS Major.', 3, 'ECE', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the ECE department.'),
  ('INFO 324', 'Introduction to Clinical Health Data Science', 'Fundamentals of clinical health informatics and quantitative analysis of clinical health data.', 4, 'INFO', '{}', '{}', 'Approved outside elective for the CS Major. Taught in the same classroom as COMPSCI 524 but evaluated independently.'),
  ('LINGUIST 401', 'Intro to Syntax', 'Approved outside elective for the CS Major.', 3, 'LINGUIST', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the Linguistics department.'),
  ('MATH 411', 'Intro to Abstract Algebra I', 'Approved outside elective for the CS Major.', 3, 'MATH', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the Math department.'),
  ('MATH 545', 'Linear Algebra for Applied Mathematics', 'Approved outside elective for the CS Major; also a COMPSCI 589 prerequisite.', 3, 'MATH', '{}', '{}', 'Waivable for COMPSCI 589 via MATH 235 + MATH 233 (both B+). Not detailed in the CICS catalog excerpt otherwise.'),
  ('MATH 551', 'Intro to Scientific Computing', 'Approved outside elective for the CS Major.', 3, 'MATH', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the Math department.'),
  ('MATH 552', 'Applications for Scientific Computing', 'Approved outside elective for the CS Major.', 3, 'MATH', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the Math department.'),
  ('MATH 571', 'Introduction to Mathematical Cryptography', 'Approved outside elective for the CS Major.', 3, 'MATH', '{}', '{}', 'Not detailed in the CICS catalog excerpt — verify prereqs directly with the Math department.'),
  -- Lab science options (titles per the requirements doc; not in the CICS catalog excerpt)
  ('CHEM 111', 'General Chemistry - Science Majors', 'Lab science option.', 4, 'CHEM', '{}', '{}', 'Pick CHEM 111 or CHEM 121, not both, for the first-semester slot. Credits approximate.'),
  ('CHEM 121', 'General Chemistry - Science Majors (alt)', 'Lab science option.', 4, 'CHEM', '{}', '{}', 'Alternative to CHEM 111. Credits approximate.'),
  ('CHEM 112', 'General Chemistry - Science Majors (2nd semester)', 'Lab science option.', 4, 'CHEM', '{}', '{}', 'Pick CHEM 112 or CHEM 122, not both. Credits approximate.'),
  ('CHEM 122', 'General Chemistry (2nd semester, alt)', 'Lab science option.', 4, 'CHEM', '{}', '{}', 'Alternative to CHEM 112. Credits approximate.'),
  ('GEOL 101', 'The Earth (with lab)', 'Lab science option, self-contained with lab.', 4, 'GEOL', '{}', '{}', 'Credits approximate.'),
  ('GEOL 103', 'Oceanography', 'Lab science option; pair with GEOL 131 for the lab component.', 3, 'GEOL', '{}', '{}', 'Must be paired with GEOL 131 (lab) to satisfy the requirement together. Credits approximate.'),
  ('GEOL 131', 'Experiencing Geology (lab)', '1-credit lab pairing with GEOL 103 or GEOL 105.', 1, 'GEOL', '{}', '{}', 'Only counts toward the Lab Science Requirement when paired with GEOL 103 or GEOL 105.'),
  ('GEOL 105', 'The Dynamic Earth', 'Lab science option; pair with GEOL 131 for the lab component.', 3, 'GEOL', '{}', '{}', 'Must be paired with GEOL 131 (lab) to satisfy the requirement together. Credits approximate.'),
  ('PHYSICS 151', 'General Physics I', 'Lab science option.', 4, 'PHYSICS', '{}', '{}', 'Alternative to PHYSICS 181. Credits approximate.'),
  ('PHYSICS 181', 'Physics I - Mechanics', 'Lab science option.', 4, 'PHYSICS', '{}', '{}', 'Alternative to PHYSICS 151. Credits approximate.'),
  ('PHYSICS 152', 'General Physics II', 'Lab science option.', 4, 'PHYSICS', '{}', '{}', 'Alternative to PHYSICS 182. Credits approximate.'),
  ('PHYSICS 182', 'Physics II - Electricity and Magnetism', 'Lab science option.', 4, 'PHYSICS', '{}', '{}', 'Alternative to PHYSICS 152. Credits approximate.'),
  -- Legacy / alternate-path / external stub courses, kept only as prerequisite targets
  ('COMPSCI 187', 'Programming with Data Structures (legacy)', 'Legacy course code, effectively superseded by CICS 210.', 4, 'COMPSCI', '{}', '{}', 'Kept only because it is still explicitly accepted as an alternate prerequisite across many current course listings.'),
  ('COMPSCI 186', 'Legacy Programming Course', 'Legacy course code referenced as an alternate prerequisite.', 4, 'COMPSCI', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted legacy alternate prerequisite.'),
  ('COMPSCI 121', 'Legacy Intro Programming Course', 'Legacy course code referenced as an alternate prerequisite.', 4, 'COMPSCI', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted legacy alternate prerequisite.'),
  ('MATH 455', 'Discrete Mathematical Structures (approx.)', 'Alternate prerequisite path to COMPSCI 311 / COMPSCI 575.', 3, 'MATH', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted alternate prerequisite.'),
  ('ENGLWRIT 112', 'College Writing', 'Gen-ed written communication requirement; also a prerequisite for CICS 305 and COMPSCI 363.', 3, 'ENGLWRIT', '{}', '{}', ''),
  ('LINGUIST 429B', 'Intro to Syntax (alternate path)', 'Alternate prerequisite path to COMPSCI 485.', 3, 'LINGUIST', '{}', '{}', 'Previously numbered LINGUIST 492B. Not detailed in the CICS catalog excerpt otherwise.'),
  ('COMPSCI 365', 'Legacy Forensics/Security Course', 'Alternate prerequisite path to COMPSCI 565.', 3, 'COMPSCI', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted alternate prerequisite.'),
  ('E&C-ENG 241', 'Legacy Systems Course', 'Alternate prerequisite path to COMPSCI 250.', 3, 'ECE', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted alternate prerequisite.'),
  ('E&C-ENG 322', 'Legacy Systems Course', 'Alternate prerequisite path to COMPSCI 367 / 590AF.', 3, 'ECE', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted alternate prerequisite.'),
  ('COMPSCI 497P', 'Legacy Distributed Systems Course', 'Alternate prerequisite path to COMPSCI 461.', 3, 'COMPSCI', '{}', '{}', 'Not detailed in the CICS catalog excerpt; kept only as an accepted alternate prerequisite.'),
  ('INFO 248', 'Intro to Data Science', 'Alternate prerequisite path to INFO 324.', 4, 'INFO', '{}', '{}', 'Not fully modeled here — its own prerequisite chain pulls in several other majors'' statistics courses (PSYCH 240, OIM 240, SOCIOL 212, etc.); verify with the INFO department if relevant.')
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
--  different group_ids are alternative (OR'd) paths. min_grade defaults to
--  'C' per "with a grade of C or better" language throughout the catalog;
--  set explicitly only when the catalog requires something else.)
-- ---------------------------------------------------------------------------
insert into public.course_prerequisites (course_code, prereq_code, group_id, min_grade) values
  ('CICS 160', 'CICS 110', 0, 'C'),
  ('CICS 160', 'COMPSCI 121', 1, 'C'),
  ('CICS 210', 'CICS 160', 0, 'C'),
  ('CICS 256', 'CICS 210', 0, 'C'),
  ('CICS 256', 'COMPSCI 187', 1, 'C'),
  ('CICS 305', 'ENGLWRIT 112', 0, 'C'), ('CICS 305', 'COMPSCI 220', 0, 'C'), ('CICS 305', 'COMPSCI 230', 0, 'C'), ('CICS 305', 'COMPSCI 240', 0, 'C'),
  ('CICS 305', 'ENGLWRIT 112', 1, 'C'), ('CICS 305', 'COMPSCI 220', 1, 'C'), ('CICS 305', 'COMPSCI 230', 1, 'C'), ('CICS 305', 'COMPSCI 250', 1, 'C'),
  ('COMPSCI 198C', 'CICS 160', 0, 'C'),
  ('COMPSCI 198C', 'COMPSCI 186', 1, 'C'),
  ('COMPSCI 198C', 'CICS 210', 2, 'C'),
  ('COMPSCI 198C', 'COMPSCI 121', 3, 'B'),
  ('COMPSCI 220', 'CICS 210', 0, 'C'),
  ('COMPSCI 220', 'COMPSCI 187', 1, 'C'),
  ('COMPSCI 230', 'CICS 210', 0, 'C'), ('COMPSCI 230', 'COMPSCI 198C', 0, 'C'),
  ('COMPSCI 230', 'COMPSCI 187', 1, 'C'), ('COMPSCI 230', 'COMPSCI 198C', 1, 'C'),
  ('COMPSCI 240', 'CICS 160', 0, 'C'), ('COMPSCI 240', 'MATH 132', 0, 'C'),
  ('COMPSCI 240', 'COMPSCI 187', 1, 'C'), ('COMPSCI 240', 'MATH 132', 1, 'C'),
  ('COMPSCI 240', 'CICS 210', 2, 'C'), ('COMPSCI 240', 'MATH 132', 2, 'C'),
  ('COMPSCI 250', 'CICS 160', 0, 'C'), ('COMPSCI 250', 'MATH 132', 0, 'C'),
  ('COMPSCI 250', 'COMPSCI 187', 1, 'C'), ('COMPSCI 250', 'MATH 132', 1, 'C'),
  ('COMPSCI 250', 'E&C-ENG 241', 2, 'C'), ('COMPSCI 250', 'MATH 132', 2, 'C'),
  ('COMPSCI 250', 'CICS 210', 3, 'C'), ('COMPSCI 250', 'MATH 132', 3, 'C'),
  ('COMPSCI 311', 'CICS 210', 0, 'C'), ('COMPSCI 311', 'COMPSCI 250', 0, 'C'),
  ('COMPSCI 311', 'CICS 210', 1, 'C'), ('COMPSCI 311', 'MATH 455', 1, 'C'),
  ('COMPSCI 311', 'COMPSCI 187', 2, 'C'), ('COMPSCI 311', 'COMPSCI 250', 2, 'C'),
  ('COMPSCI 311', 'COMPSCI 187', 3, 'C'), ('COMPSCI 311', 'MATH 455', 3, 'C'),
  ('COMPSCI 320', 'COMPSCI 220', 0, 'C'),
  ('COMPSCI 325', 'COMPSCI 187', 0, 'C'),
  ('COMPSCI 325', 'CICS 210', 1, 'C'),
  ('COMPSCI 326', 'COMPSCI 220', 0, 'C'),
  ('COMPSCI 328', 'CICS 210', 0, 'C'),
  ('COMPSCI 328', 'COMPSCI 187', 1, 'C'),
  ('COMPSCI 335', 'COMPSCI 220', 0, 'C'),
  ('COMPSCI 335', 'COMPSCI 230', 1, 'C'),
  ('COMPSCI 345', 'CICS 210', 0, 'C'),
  ('COMPSCI 345', 'COMPSCI 187', 1, 'C'),
  ('COMPSCI 360', 'COMPSCI 230', 0, 'C'),
  ('COMPSCI 363', 'COMPSCI 230', 0, 'C'), ('COMPSCI 363', 'ENGLWRIT 112', 0, 'C'),
  ('COMPSCI 367', 'COMPSCI 230', 0, 'C'),
  ('COMPSCI 367', 'E&C-ENG 322', 1, 'C'),
  ('COMPSCI 377', 'COMPSCI 230', 0, 'C'),
  ('COMPSCI 383', 'CICS 210', 0, 'C'), ('COMPSCI 383', 'COMPSCI 240', 0, 'C'),
  ('COMPSCI 383', 'CICS 210', 1, 'C'), ('COMPSCI 383', 'STATISTC 315', 1, 'C'),
  ('COMPSCI 383', 'COMPSCI 187', 2, 'C'), ('COMPSCI 383', 'COMPSCI 240', 2, 'C'),
  ('COMPSCI 383', 'COMPSCI 187', 3, 'C'), ('COMPSCI 383', 'STATISTC 315', 3, 'C'),
  ('COMPSCI 389', 'CICS 210', 0, 'C'), ('COMPSCI 389', 'COMPSCI 240', 0, 'C'), ('COMPSCI 389', 'MATH 132', 0, 'C'),
  ('COMPSCI 389', 'CICS 210', 1, 'C'), ('COMPSCI 389', 'STATISTC 315', 1, 'C'), ('COMPSCI 389', 'MATH 132', 1, 'C'),
  ('COMPSCI 420', 'COMPSCI 320', 0, 'C'),
  ('COMPSCI 420', 'COMPSCI 326', 1, 'C'),
  ('COMPSCI 429', 'COMPSCI 320', 0, 'B'),
  ('COMPSCI 445', 'COMPSCI 220', 0, 'C'), ('COMPSCI 445', 'COMPSCI 311', 0, 'C'), ('COMPSCI 445', 'COMPSCI 345', 0, 'C'),
  ('COMPSCI 445', 'COMPSCI 230', 1, 'C'), ('COMPSCI 445', 'COMPSCI 311', 1, 'C'), ('COMPSCI 445', 'COMPSCI 345', 1, 'C'),
  ('COMPSCI 453', 'COMPSCI 230', 0, 'C'),
  ('COMPSCI 453', 'COMPSCI 377', 1, 'C'),
  ('COMPSCI 461', 'COMPSCI 326', 0, 'C'),
  ('COMPSCI 461', 'COMPSCI 345', 1, 'C'),
  ('COMPSCI 461', 'COMPSCI 377', 2, 'C'),
  ('COMPSCI 461', 'COMPSCI 453', 3, 'C'),
  ('COMPSCI 461', 'COMPSCI 497P', 4, 'C'),
  ('COMPSCI 485', 'COMPSCI 220', 0, 'C'), ('COMPSCI 485', 'COMPSCI 240', 0, 'C'),
  ('COMPSCI 485', 'LINGUIST 429B', 1, 'C'),
  ('COMPSCI 491P', 'COMPSCI 250', 0, 'C'), ('COMPSCI 491P', 'COMPSCI 383', 0, 'C'),
  ('COMPSCI 491P', 'COMPSCI 250', 1, 'C'), ('COMPSCI 491P', 'COMPSCI 389', 1, 'C'),
  ('COMPSCI 514', 'COMPSCI 240', 0, 'B+'), ('COMPSCI 514', 'COMPSCI 311', 0, 'B+'),
  ('COMPSCI 514', 'COMPSCI 240', 1, 'C'), ('COMPSCI 514', 'STATISTC 315', 1, 'C'), ('COMPSCI 514', 'COMPSCI 311', 1, 'C'), ('COMPSCI 514', 'MATH 233', 1, 'C'), ('COMPSCI 514', 'MATH 235', 1, 'C'),
  ('COMPSCI 515', 'COMPSCI 240', 0, 'C'), ('COMPSCI 515', 'COMPSCI 250', 0, 'C'),
  ('COMPSCI 520', 'COMPSCI 320', 0, 'C'),
  ('COMPSCI 520', 'COMPSCI 220', 1, 'C'), ('COMPSCI 520', 'COMPSCI 326', 1, 'C'),
  ('COMPSCI 532', 'COMPSCI 377', 0, 'C'), ('COMPSCI 532', 'COMPSCI 445', 0, 'C'),
  ('COMPSCI 550', 'CICS 210', 0, 'C'), ('COMPSCI 550', 'STATISTC 315', 0, 'C'),
  ('COMPSCI 550', 'COMPSCI 187', 1, 'C'), ('COMPSCI 550', 'STATISTC 315', 1, 'C'),
  ('COMPSCI 565', 'COMPSCI 365', 0, 'C'),
  ('COMPSCI 565', 'COMPSCI 377', 1, 'C'),
  ('COMPSCI 571', 'COMPSCI 220', 0, 'C'),
  ('COMPSCI 571', 'COMPSCI 230', 1, 'C'),
  ('COMPSCI 571', 'COMPSCI 326', 2, 'C'),
  ('COMPSCI 575', 'COMPSCI 250', 0, 'B'),
  ('COMPSCI 575', 'MATH 455', 1, 'B'),
  ('COMPSCI 589', 'MATH 545', 0, 'C'), ('COMPSCI 589', 'COMPSCI 240', 0, 'C'), ('COMPSCI 589', 'STATISTC 315', 0, 'C'),
  ('COMPSCI 590AF', 'COMPSCI 230', 0, 'C'),
  ('COMPSCI 590AF', 'E&C-ENG 322', 1, 'C'),
  ('COMPSCI 590Q', 'MATH 235', 0, 'C'),
  ('INFO 324', 'INFO 248', 0, 'C'),
  ('INFO 324', 'STATISTC 315', 1, 'C'),
  ('INFO 324', 'COMPSCI 240', 2, 'C'),
  ('MATH 132', 'MATH 131', 0, 'C'),
  ('MATH 233', 'MATH 132', 0, 'C'),
  ('MATH 235', 'MATH 131', 0, 'C')
on conflict (course_code, prereq_code, group_id) do nothing;

-- ---------------------------------------------------------------------------
-- Degree program + requirement categories
-- ---------------------------------------------------------------------------
insert into public.degree_programs (name, program_type, description) values
  ('BS Computer Science', 'major', 'UMass Amherst BS in Computer Science, per the CICS degree requirements page.')
on conflict (name) do nothing;

with cs as (select id from public.degree_programs where name = 'BS Computer Science')
insert into public.requirement_categories (program_id, name, description, min_courses, sort_order)
select cs.id, v.name, v.description, v.min_courses, v.sort_order
from cs, (values
  ('Introductory Programming Sequence', 'CICS 110 -> CICS 160 -> CICS 210.', 3, 0),
  ('Core Computer Science Courses', 'COMPSCI 220, 230, 240, 250.', 4, 1),
  ('Mathematics Foundation', 'MATH 131, 132, 235, plus MATH 233 or STATISTC 315 for the 4th slot (STATISTC 315 does not replace MATH 132).', 4, 2),
  ('Algorithms Requirement', 'COMPSCI 311, required for the BS (prereq: COMPSCI 250).', 1, 3),
  ('CS Electives (300-399)', '3 additional CS electives numbered 300+; may include one satisfying the Integrative Experience requirement.', 3, 4),
  ('CS Electives (400+)', '3 additional CS electives numbered 400 or above.', 3, 5),
  ('Additional Elective (300+ or approved outside)', '1 more CS elective numbered 300+, or a course from the approved outside-department list.', 1, 6),
  ('Integrative Experience (IE) Requirement', 'Satisfied by COMPSCI 320 or COMPSCI 326, which also count as CS Electives (same course, double duty).', 1, 7),
  ('Junior Year Writing (JYW) Requirement', 'CICS 305 for CS primary majors; double majors with CS as secondary may substitute their primary major''s JYW course.', 1, 8),
  ('Lab Science Requirement', '2 courses (8 credits) from the approved lab-science list; mixing departments is fine.', 2, 9)
) as v(name, description, min_courses, sort_order)
on conflict (program_id, name) do nothing;

-- ---------------------------------------------------------------------------
-- Which courses satisfy which category
-- ---------------------------------------------------------------------------
insert into public.requirement_courses (category_id, course_code, satisfies_note)
select rc.id, v.course_code, v.note
from public.requirement_categories rc
join public.degree_programs dp on dp.id = rc.program_id
join (values
  ('Introductory Programming Sequence', 'CICS 110', ''),
  ('Introductory Programming Sequence', 'CICS 160', ''),
  ('Introductory Programming Sequence', 'CICS 210', ''),

  ('Core Computer Science Courses', 'COMPSCI 220', ''),
  ('Core Computer Science Courses', 'COMPSCI 230', ''),
  ('Core Computer Science Courses', 'COMPSCI 240', ''),
  ('Core Computer Science Courses', 'COMPSCI 250', ''),

  ('Mathematics Foundation', 'MATH 131', ''),
  ('Mathematics Foundation', 'MATH 132', ''),
  ('Mathematics Foundation', 'MATH 235', ''),
  ('Mathematics Foundation', 'MATH 233', 'Alternative to STATISTC 315 for the 4th slot.'),
  ('Mathematics Foundation', 'STATISTC 315', 'Alternative to MATH 233 for the 4th slot; does not replace MATH 132.'),

  ('Algorithms Requirement', 'COMPSCI 311', ''),

  ('CS Electives (300-399)', 'COMPSCI 320', 'Also satisfies the IE Requirement (same course, not an extra one).'),
  ('CS Electives (300-399)', 'COMPSCI 325', ''),
  ('CS Electives (300-399)', 'COMPSCI 326', 'Also satisfies the IE Requirement (same course, not an extra one).'),
  ('CS Electives (300-399)', 'COMPSCI 328', ''),
  ('CS Electives (300-399)', 'COMPSCI 335', ''),
  ('CS Electives (300-399)', 'COMPSCI 345', ''),
  ('CS Electives (300-399)', 'COMPSCI 360', ''),
  ('CS Electives (300-399)', 'COMPSCI 363', ''),
  ('CS Electives (300-399)', 'COMPSCI 367', 'Does not count as an INFORM elective, only a CS one.'),
  ('CS Electives (300-399)', 'COMPSCI 377', ''),
  ('CS Electives (300-399)', 'COMPSCI 383', ''),
  ('CS Electives (300-399)', 'COMPSCI 389', ''),

  ('CS Electives (400+)', 'COMPSCI 420', ''),
  ('CS Electives (400+)', 'COMPSCI 429', 'Permission-only enrollment, requires a B or better in a prior COMPSCI 320.'),
  ('CS Electives (400+)', 'COMPSCI 445', ''),
  ('CS Electives (400+)', 'COMPSCI 453', ''),
  ('CS Electives (400+)', 'COMPSCI 461', ''),
  ('CS Electives (400+)', 'COMPSCI 485', ''),
  ('CS Electives (400+)', 'COMPSCI 491P', ''),
  ('CS Electives (400+)', 'COMPSCI 514', ''),
  ('CS Electives (400+)', 'COMPSCI 515', ''),
  ('CS Electives (400+)', 'COMPSCI 520', ''),
  ('CS Electives (400+)', 'COMPSCI 532', ''),
  ('CS Electives (400+)', 'COMPSCI 550', ''),
  ('CS Electives (400+)', 'COMPSCI 565', ''),
  ('CS Electives (400+)', 'COMPSCI 571', ''),
  ('CS Electives (400+)', 'COMPSCI 575', ''),
  ('CS Electives (400+)', 'COMPSCI 589', ''),
  ('CS Electives (400+)', 'COMPSCI 590AF', ''),
  ('CS Electives (400+)', 'COMPSCI 590OP', ''),
  ('CS Electives (400+)', 'COMPSCI 590Q', ''),
  -- NOTE: COMPSCI 590RM is intentionally NOT listed here - the catalog
  -- explicitly says it does not count as a CS elective for the BS/BA.

  ('Additional Elective (300+ or approved outside)', 'COMPSCI 320', ''),
  ('Additional Elective (300+ or approved outside)', 'COMPSCI 326', ''),
  ('Additional Elective (300+ or approved outside)', 'COMPSCI 345', ''),
  ('Additional Elective (300+ or approved outside)', 'COMPSCI 445', ''),
  ('Additional Elective (300+ or approved outside)', 'ECE 353', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'ECE 547', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'ECE 668', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'INFO 324', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'LINGUIST 401', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'MATH 411', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'MATH 545', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'MATH 551', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'MATH 552', 'Approved outside elective.'),
  ('Additional Elective (300+ or approved outside)', 'MATH 571', 'Approved outside elective.'),

  ('Integrative Experience (IE) Requirement', 'COMPSCI 320', ''),
  ('Integrative Experience (IE) Requirement', 'COMPSCI 326', ''),

  ('Junior Year Writing (JYW) Requirement', 'CICS 305', ''),

  ('Lab Science Requirement', 'CICS 256', ''),
  ('Lab Science Requirement', 'CHEM 111', ''),
  ('Lab Science Requirement', 'CHEM 121', ''),
  ('Lab Science Requirement', 'CHEM 112', ''),
  ('Lab Science Requirement', 'CHEM 122', ''),
  ('Lab Science Requirement', 'GEOL 101', ''),
  ('Lab Science Requirement', 'GEOL 103', 'Pair with GEOL 131 for the lab component.'),
  ('Lab Science Requirement', 'GEOL 131', 'Only counts when paired with GEOL 103 or GEOL 105.'),
  ('Lab Science Requirement', 'GEOL 105', 'Pair with GEOL 131 for the lab component.'),
  ('Lab Science Requirement', 'PHYSICS 151', ''),
  ('Lab Science Requirement', 'PHYSICS 181', ''),
  ('Lab Science Requirement', 'PHYSICS 152', ''),
  ('Lab Science Requirement', 'PHYSICS 182', '')
) as v(category_name, course_code, note)
  on dp.name = 'BS Computer Science' and rc.name = v.category_name
on conflict (category_id, course_code) do nothing;

commit;
