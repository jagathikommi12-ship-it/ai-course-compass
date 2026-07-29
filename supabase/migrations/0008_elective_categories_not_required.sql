-- The Mathematics Foundation fix (0007) only handled one "mixed" category.
-- These five categories are pure "pick N of M" electives where NO single
-- course should be flagged as individually required — every course listed
-- under them is one option among several, not something you must take.
update public.requirement_courses rc
set is_required = false
from public.requirement_categories cat
where rc.category_id = cat.id
  and cat.name in (
    'CS Electives (300-399)',
    'CS Electives (400+)',
    'Additional Elective (300+ or approved outside)',
    'Integrative Experience (IE) Requirement',
    'Lab Science Requirement'
  );
