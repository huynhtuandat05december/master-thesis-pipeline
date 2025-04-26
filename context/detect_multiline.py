import re

from schema.common import Position
from post_processing.utils import indentation, get_last_line, lines, FUNCTION_KEYWORDS, \
    FUNCTION_OR_METHOD_INVOCATION_REGEX, OPENING_BRACKET_REGEX
from programing_language import get_language_config, ProgrammingLanguage

LANGUAGES_WITH_MULTILINE_SUPPORT = [
    'astro',
    'c',
    'cpp',
    'c_sharp',
    'css',
    'dart',
    'elixir',
    'go',
    'html',
    'java',
    'javascript',
    'javascriptreact',
    'kotlin',
    'php',
    'python',
    'rust',
    'svelte',
    'typescript',
    'typescriptreact',
    'vue'
]


def ends_with_block_start(text, language_id):
    language_config = get_language_config(language_id)
    if language_config and language_config.get('block_start'):
        block_start = language_config['block_start']
        if text.rstrip().endswith(block_start):
            return block_start
    return None


def start_with_block_end(text, language_id):
    language_config = get_language_config(language_id)
    if language_config and language_config.get('block_end'):
        block_end = language_config['block_end']
        if text.lstrip().startswith(block_end):
            return block_end
    return None


def detect_multiline(params):
    doc_context = params['doc_context']
    language_id = params['language_id']
    position = params['position']

    current_line_prefix = doc_context['current_line_prefix']
    current_line_suffix = doc_context['current_line_suffix']

    is_multiline_supported = language_id in LANGUAGES_WITH_MULTILINE_SUPPORT
    current_line_text = (
            current_line_suffix.strip() + current_line_prefix) if current_line_suffix.strip() else current_line_prefix

    is_method_or_function_invocation = not re.search(FUNCTION_KEYWORDS, current_line_prefix.strip()) and re.search(
        FUNCTION_OR_METHOD_INVOCATION_REGEX, current_line_text)

    if is_method_or_function_invocation or not is_multiline_supported:
        return {'multiline_trigger': None, 'multiline_trigger_position': None}

    result_start_empty_block = detect_start_empty_block(doc_context=doc_context, language_id=language_id,
                                                     position=position)
    if result_start_empty_block:
        return result_start_empty_block

    result_open_bracket = detect_open_bracket(doc_context=doc_context, language_id=language_id,
                                                     position=position)
    if result_open_bracket:
        return result_open_bracket

    result_start_non_empty_block = detect_start_non_empty_block(doc_context=doc_context, language_id=language_id, position=position)
    if result_start_non_empty_block:
        return result_start_non_empty_block

    return {'multiline_trigger': None, 'multiline_trigger_position': None}


def detect_start_empty_block(doc_context, language_id, position):
    prefix = doc_context['prefix']
    prev_non_empty_line = doc_context['prev_non_empty_line']
    next_non_empty_line = doc_context['next_non_empty_line']
    current_line_prefix = doc_context['current_line_prefix']
    current_line_suffix = doc_context['current_line_suffix']


    block_start = ends_with_block_start(prefix, language_id)
    is_block_start_active = bool(block_start)

    non_empty_line_ends_with_block_start = (
            current_line_prefix.strip() and
            is_block_start_active and
            indentation(current_line_prefix) >= indentation(next_non_empty_line)
    )

    is_empty_line_after_block_start = (
            not current_line_prefix.strip() and
            not current_line_suffix.strip() and
            is_block_start_active and
            indentation(current_line_prefix) > indentation(prev_non_empty_line) >= indentation(
        next_non_empty_line)
    )

    if non_empty_line_ends_with_block_start or is_empty_line_after_block_start:
        
        return {
            'multiline_trigger': block_start,
            'multiline_trigger_position': get_prefix_last_non_empty_char_position(prefix, position),
        }

    return None


def detect_open_bracket(doc_context, language_id, position):
    prefix = doc_context['prefix']
    prev_non_empty_line = doc_context['prev_non_empty_line']
    next_non_empty_line = doc_context['next_non_empty_line']
    current_line_prefix = doc_context['current_line_prefix']
    current_line_suffix = doc_context['current_line_suffix']

    opening_bracket_match = re.search(OPENING_BRACKET_REGEX, get_last_line(prefix.strip()))

    is_same_line_opening_bracket_match = (
            current_line_prefix.strip() and
            opening_bracket_match and
            indentation(current_line_prefix) >= indentation(next_non_empty_line)
    )

    is_new_line_opening_bracket_match = (
            not current_line_prefix.strip() and
            not current_line_suffix.strip() and
            opening_bracket_match and
            indentation(current_line_prefix) > indentation(prev_non_empty_line) >= indentation(
        next_non_empty_line)
    )

    if is_new_line_opening_bracket_match or is_same_line_opening_bracket_match:
        
        return {
            'multiline_trigger': opening_bracket_match.group(0),
            'multiline_trigger_position': get_prefix_last_non_empty_char_position(prefix, position),
            
        }


def detect_start_non_empty_block(doc_context, language_id, position):
    prefix = doc_context['prefix']
    next_non_empty_line = doc_context['next_non_empty_line']
    current_line_prefix = doc_context['current_line_prefix']
    block_end = start_with_block_end(next_non_empty_line, language_id)

    if block_end and indentation(current_line_prefix) >= indentation(next_non_empty_line):
        
        position_block_start = find_block_start(language_id, prefix, current_line_prefix, position)
        return {
            'multiline_trigger': position_block_start['multiline_trigger'],
            'multiline_trigger_position': position_block_start['multiline_trigger_position'],
            
        }


def get_prefix_last_non_empty_char_position(prefix: str, cursor_position: Position):
    trimmed_prefix = prefix.rstrip()
    diff_length = len(prefix) - len(trimmed_prefix)

    if diff_length == 0:
        return cursor_position.translate(0, -1)

    prefix_diff = prefix[-diff_length:]
    return Position(
        cursor_position.line - (len(lines(prefix_diff)) - 1),
        len(get_last_line(trimmed_prefix)) - 1
    )


def find_block_start(language_id, prefix, current_line_prefix, cursor_position):
    language_config = get_language_config(language_id)
    block_start = None
    if language_config and language_config.get('block_start'):
        block_start = language_config['block_start']

    if not block_start:
        return {
            "multiline_trigger": None,
            "multiline_trigger_position": None,
            "line": None
        }

    lines_of_prefix = lines(prefix)
    reverse_lines_of_prefix = lines_of_prefix[::-1]
    for i, line in enumerate(reverse_lines_of_prefix):
        if block_start in line and indentation(line) < indentation(current_line_prefix):
            return {
                "multiline_trigger": block_start,
                "multiline_trigger_position": Position(cursor_position.line - i, len(line.rstrip()) - 1),
                "line": line
            }

    return {
        "multiline_trigger": None,
        "multiline_trigger_position": None,
        "line": None
    }


def is_python_end_block_scope(language_id, prefix, current_line_prefix, position, next_non_empty_line):
    line_start_block = find_block_start(language_id, prefix, current_line_prefix, position, )['line']
    if line_start_block is None:
        return False

    if indentation(current_line_prefix) > indentation(line_start_block) >= indentation(
            next_non_empty_line):
        return True

    return False
