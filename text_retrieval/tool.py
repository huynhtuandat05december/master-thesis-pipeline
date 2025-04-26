import os
import glob
from schema.common import Document

def last_n_lines(text: str, n: int) -> str:
    """Return the last n lines of the text"""
    lines = text.splitlines()
    return '\n'.join(lines[-n:]) if lines else ''

def read_code(fname):
    with open(fname, 'r', encoding='utf8') as f:
        return f.read()

def iterate_repository(base_dir = '', repo = 'test', target_file = None):
    pattern = os.path.join(f'{base_dir}/{repo}', "**", "*.py")
    files = glob.glob(pattern, recursive=True)

    skipped_files = []
    result = []
    for fname in files:
        try:
            if target_file and target_file == fname:
                continue
            code = read_code(fname)
            document = Document(uri=fname, language_id="python", text=code)
            result.append(document)
        except Exception as e:
            skipped_files.append((fname, e))
            continue

    if len(skipped_files) > 0:
        print(f"Skipped {len(skipped_files)} out of {len(files)} files due to I/O errors")
        for fname, e in skipped_files:
            print(f"{fname}: {e}")
    return result

if __name__ == "__main__":
    result = iterate_repository()
    print(result)