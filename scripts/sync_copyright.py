import re
import sys
import subprocess

CLEANUP_REGEX = re.compile(r"(#\s*Copyright\s*\(c\)\s*)([^,]+)(,.*)")

def get_git_years(filepath):
    try:
        cmd = ["git", "log", "--follow", "--format=%ad", "--date=format:%Y",
               "--", filepath]
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
        if not output:
            return None, None

        history = output.splitlines()
        return str(history[-1]), str(history[0])
    except Exception:
        return None, None

def sync_file(filepath):
    first, last = get_git_years(filepath)
    if not first:
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        match = CLEANUP_REGEX.search(line)
        if match:
            prefix = match.group(1)
            suffix = match.group(3)

            date_part = f"{first}-{last}" if first != last else f"{first}"
            new_line = f"{prefix}{date_part}{suffix}\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Cleaned and Synced: {filepath} ({first}-{last})")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        sync_file(arg)
