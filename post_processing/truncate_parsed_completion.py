from .parse_completion import parse_completion
from .utils import BRACKET_PAIR, check_bracket_in_new_line


def insert_missing_brackets(text):
    opening_stack = []
    bracket_pairs = list(BRACKET_PAIR.items())

    for char in text:
        bracket_pair = next((bp for bp in bracket_pairs if bp[1] == char), None)

        if bracket_pair:
            if opening_stack and opening_stack[-1] == bracket_pair[0]:
                opening_stack.pop()
        elif char in BRACKET_PAIR:
            opening_stack.append(char)

    return text + ''.join(BRACKET_PAIR[open_bracket] for open_bracket in reversed(opening_stack))


# Assuming these placeholder definitions for handling a parse tree and managing contexts
def truncate_parsed_completion(context):
    completion = context['completion']
    document = context['document']
    doc_context = context['doc_context']
    language_id = document.language_id

    if not (completion.get('tree') and completion.get('points')):
        raise ValueError('Expected completion and document to have tree-sitter data for truncation')

    insert_text = completion['insert_text']
    points = completion['points']

    fixed_completion = completion
    insert_text_with_missing_brackets = insert_missing_brackets(doc_context['current_line_prefix'] + insert_text)[
                                        len(doc_context['current_line_prefix']):]

    if len(insert_text_with_missing_brackets) != len(insert_text):
        updated_completion = parse_completion({
            'completion': {'insert_text': insert_text_with_missing_brackets},
            'document': document,
            'doc_context': doc_context,
        })
        if fixed_completion.get('tree'):
            fixed_completion = updated_completion

    node_to_insert = find_last_ancestor_on_the_same_row(
        fixed_completion['tree'].root_node,
        points.get('trigger', points.get('start')),
        insert_text,
        language_id
    )

    result = {
        'insert_text': insert_text,
        'node_to_insert': node_to_insert if node_to_insert else None
    }
    if node_to_insert:
        overlap = find_largest_suffix_prefix_overlap(node_to_insert.text.decode("utf-8"), insert_text.strip())
        if overlap:
            result = {
                'insert_text': overlap,
                'node_to_insert': node_to_insert,
            }
    check_final_completion = parse_completion({
        'completion': result,
        'document': document,
        'doc_context': doc_context,
    })
    error_count = check_final_completion.get('parse_error_count', 0)
    result['error_count'] = error_count

    return result


def find_last_ancestor_on_the_same_row(root, start_point, insert_text,language_id):
    initial = root.descendant_for_point_range(start_point, start_point)
    current = initial

    while (current and
           current.parent and
           (current.parent.start_point[0] == initial.start_point[0] or (check_bracket_in_new_line(insert_text, language_id) and current.parent.start_point[0] + 1 == initial.start_point[0])) and
           current.parent.grammar_id != root.grammar_id):
        current = current.parent
    return current


def find_largest_suffix_prefix_overlap(left: str, right: str) -> str:
    overlap = ''

    for i in range(1, min(len(left), len(right)) + 1):
        suffix = left[-i:]
        prefix = right[:i]

        if suffix == prefix:
            overlap = suffix

    if len(overlap) == 0:
        return None

    return overlap