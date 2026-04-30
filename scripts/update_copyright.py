import re
import sys
from datetime import datetime

# Current year
CURRENT_YEAR = str(datetime.now().year)
COPYRIGHT_REGEX = re.compile(r"(#\s*Copyright\s*\(c\)\s*)(\d{4})(-\d{4})?(.*)")

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replace_year(match):
        prefix = match.group(1)
        start_year = match.group(2)
        suffix = match.group(4)

        if start_year == CURRENT_YEAR:
            return f"{prefix}{start_year}{suffix}"

        return f"{prefix}{start_year}-{CURRENT_YEAR}{suffix}"

    new_content = COPYRIGHT_REGEX.sub(replace_year, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        update_file(arg)
