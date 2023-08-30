import re

from ics import Calendar
import glob


def parse_ics_with_updated_format(file_path):
    course_codes = {}
    with open(file_path, "r", encoding="utf-8") as f:
        calendar_content = f.read()
        calendar = Calendar(calendar_content)
        for event in calendar.events:
            summary = event.summary
            # Attempting to extract course code and group using specific patterns
            course_code_match = re.search(r"MU4IN\d+[A-Z]*", summary)
            group_match = re.search(r"\d+$", summary)

            if course_code_match:
                course_code = course_code_match.group(0)
                # If there's no group number at the end, consider it as group 1
                group_number = 1 if group_match is None else int(group_match.group(0))

                if course_code in course_codes:
                    course_codes[course_code] = max(
                        course_codes[course_code], group_number
                    )
                else:
                    course_codes[course_code] = group_number

    return course_codes


for file_path in glob.glob("data/M1_*.ics"):
    print(file_path)
    course_codes_and_groups_updated = parse_ics_with_updated_format(file_path)
    print(course_codes_and_groups_updated)
