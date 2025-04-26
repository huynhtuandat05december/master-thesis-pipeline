import re

from schema.common import Position
from programing_language import get_language_config, ProgrammingLanguage
BRACKET_PAIR = {
    '(': ')',
    '[': ']',
    '{': '}',
    '<': '>'
}
CLOSING_BRACKET = ['}', ']', ')']
INDENTATION_REGEX = re.compile(r'^[\t ]*')
OPENING_BRACKET_REGEX = re.compile(r'([([{])$')
FUNCTION_OR_METHOD_INVOCATION_REGEX = re.compile(r'\b[^()]+\((.*)\)$')
FUNCTION_KEYWORDS = re.compile(r'^(function|def|fn|fun)')
LANGUAGE_BRACKET_IN_NEW_LINE = [
    ProgrammingLanguage.C,
    ProgrammingLanguage.CPP,
    ProgrammingLanguage.C_SHARP
]



def indentation(line, tab_size=None):
    tab_size = tab_size if tab_size is not None else 4
    match = re.match(INDENTATION_REGEX, line)
    if match:
        whitespace = match.group(0)
        return sum(tab_size if char == '\t' else 1 for char in whitespace)

    return 0


def get_last_line(text: str) -> str:
    last_lf = text.rfind("\n")
    last_crlf = text.rfind("\r\n")

    # There are no line breaks
    if last_lf == -1 and last_crlf == -1:
        return text

    return text[(last_crlf + 2 if last_crlf >= 0 else last_lf + 1):]


def get_first_line(text: str):
    first_lf = text.find('\n')
    first_crlf = text.find('\r\n')
    # There are no line breaks
    if first_lf == -1 and first_crlf == -1:
        return text
    # Use the earlier line break index if both are found, otherwise use whichever is found
    if first_crlf >= 0:
        return text[:first_crlf]
    return text[:first_lf]


def get_until_non_empty_line(text: str):
    lines = text.splitlines()
    result = ""
    for line in lines:
        result += line + '\n'
        if line.strip():
            break
    return result.rstrip('\n')


def get_until_non_empty_line_dynamic(text: str, language_id):
    lines = text.splitlines()
    result = ""
    for idx, line in enumerate(lines):
        result += line + '\n'
        if line.strip():
            if language_id in LANGUAGE_BRACKET_IN_NEW_LINE:
                language_config = get_language_config(language_id)
                if idx + 1 < len(lines) and language_config.get('block_start') == lines[idx + 1].strip():
                    result += lines[idx + 1] + '\n'
            break
    return result.rstrip('\n')


def check_bracket_in_new_line(text: str, language_id):
    text = get_until_non_empty_line_dynamic(text, language_id)
    if language_id not in LANGUAGE_BRACKET_IN_NEW_LINE:
        return False

    lines = text.splitlines()
    language_config = get_language_config(language_id)
    if lines[-1].strip() == language_config.get('block_start'):
        return True

    return False


def should_include_closing_line(prefix_indentation_with_first_completion_line, suffix):
    include_closing_line_based_on_brackets = should_include_closing_line_based_on_brackets(
        prefix_indentation_with_first_completion_line,
        suffix
    )

    start_indent = indentation(prefix_indentation_with_first_completion_line)
    next_non_empty_line = get_next_non_empty_line(suffix)

    return indentation(next_non_empty_line) < start_indent or include_closing_line_based_on_brackets


def should_include_closing_line_based_on_brackets(prefix_indentation_with_first_completion_line, suffix):
    matches = re.findall(OPENING_BRACKET_REGEX, prefix_indentation_with_first_completion_line)

    if matches:
        opening_bracket = matches[0]
        closing_bracket = BRACKET_PAIR.get(opening_bracket)

        return bool(opening_bracket) and suffix.startswith(closing_bracket)

    return False


def get_prev_non_empty_line(prefix: str) -> str:
    prev_lf = prefix.rfind("\n")
    prev_crlf = prefix.rfind("\r\n")

    # There is no previous line
    if prev_lf == -1 and prev_crlf == -1:
        return ""

    lines = prefix[:prev_crlf if prev_crlf >= 0 else prev_lf].splitlines()

    for line in reversed(lines):
        if line.strip():
            return line
    return ""


def get_next_non_empty_line(suffix):
    next_lf = suffix.find('\n')
    next_crlf = suffix.find('\r\n')

    # There is no next line
    if next_lf == -1 and next_crlf == -1:
        return ''

    # Determine which line ending to use, prioritize CRLF if found
    next_line_index = next_crlf + 2 if next_crlf != -1 else next_lf + 1

    # Get all subsequent lines
    subsequent_lines = suffix[next_line_index:].splitlines()

    # Find the first non-empty line
    for line in subsequent_lines:
        if line.strip():
            return line

    return ''


def get_first_non_empty_line(suffix: str):
    next_line_suffix = suffix[suffix.find('\n'):]

    for line in next_line_suffix.split('\n'):
        if line.strip():
            return line

    return ""


def remove_trailing_whitespace(text: str):
    return '\n'.join(line.rstrip() for line in text.split('\n'))


def trim_until_suffix(insertion: str, prefix: str, suffix: str, language_id: str):
    config = get_language_config(language_id)

    insertion = insertion.rstrip()

    first_non_empty_suffix_line = get_first_non_empty_line(suffix)

    if len(first_non_empty_suffix_line) == 0:
        return insertion

    prefix_last_new_line = prefix.rfind('\n')
    prefix_indentation_with_first_completion_line = prefix[prefix_last_new_line + 1:]
    suffix_indent = indentation(first_non_empty_suffix_line)
    start_indent = indentation(prefix_indentation_with_first_completion_line)
    has_empty_completion_line = prefix_indentation_with_first_completion_line.strip() == ''

    insertion_lines = insertion.split('\n')
    cut_off_index = len(insertion_lines)

    for i in range(len(insertion_lines) - 1, -1, -1):
        line = insertion_lines[i]

        if len(line) == 0:
            continue

        if i == 0:
            line = prefix_indentation_with_first_completion_line + line

        line_indentation = indentation(line)
        is_same_indentation = line_indentation <= suffix_indent

        if (
                has_empty_completion_line and config and
                config.get('block_end') and
                line.strip().startswith(config['block_end']) and
                start_indent == line_indentation and
                len(insertion_lines) == 1
        ):
            cut_off_index = i
            break

        if is_same_indentation and first_non_empty_suffix_line.startswith(line):
            cut_off_index = i
            break

    return '\n'.join(insertion_lines[:cut_off_index])


def collapse_duplicative_whitespace(prefix: str, completion: str) -> str:
    if prefix.endswith(' ') or prefix.endswith('\t'):
        completion = re.sub(r'^[\t ]+', '', completion)
    return completion


def lines(text: str):
    return re.split(r'\r?\n', text)


def get_position_after_text_insertion(position: Position, text: str = ''):
    if not text:
        return position

    inserted_lines = lines(text)

    if len(inserted_lines) <= 1:
        updated_position = position.translate(0, max(len(get_first_line(text)), 0))
    else:
        updated_position = Position(position.line + len(inserted_lines) - 1, len(inserted_lines[-1]))

    return updated_position


def messages_to_text(messages):
    text_parts = []
    for message in messages:
        text = f"{message['role']} {message['content']}" if message['content'] is not None else message['role']
        text_parts.append(text)
    return ''.join(text_parts)

def messages_to_text_langchain(messages):
    text_parts = []
    for message in messages:
        text = message.content
        text_parts.append(text)
    return ''.join(text_parts)


BAD_COMPLETION_START = re.compile(r"^([\U0001F300-\U0001FAFF]|\u200B|\+ |- |\. )+\s+", re.UNICODE)


def fix_bad_completion_start(completion: str) -> str:
    return BAD_COMPLETION_START.sub('', completion)
