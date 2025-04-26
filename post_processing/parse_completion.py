from typing import Tuple

from .process_inline_completion import get_matching_suffix_length
from programing_language import NODE_LANGUAGE
from tree_sitter_local.tree_sitter_local import TreeSitterAnalyzer


def parse_origin_document(context):
    document = context['document']
    language_id = document['language_id']

    parser =  TreeSitterAnalyzer(language_string=language_id)

    tree = parser.safe_parse(document['text'])
    if not tree:
        return None

    return tree

def get_nodes_for_line(tree, line_number):
    def traverse(node):
        if node.start_point[0] == line_number:
            yield node
        for child in node.children:
            yield from traverse(child)

    return list(traverse(tree.root_node))


def parse_completion(context):
    completion = context['completion']
    document = context['document']
    doc_context = context['doc_context']
    position = doc_context['position']
    multiline_trigger_position = doc_context.get('multiline_trigger_position', None)
    language_id = document.language_id

    parser = TreeSitterAnalyzer(language_string=language_id)


    tree_with_completion, completion_end_position, edit = paste_completion({
        'completion': completion,
        'document': document,
        'parser': parser,
        'doc_context': doc_context
    })

    if not tree_with_completion:
        return completion

    points = {
        'start': (position.line, position.character),
        'end': completion_end_position
    }

    if multiline_trigger_position:
        points['trigger'] = (multiline_trigger_position.line, multiline_trigger_position.character)

    node_language = NODE_LANGUAGE.get(document.language_id)
    if node_language:
        new_point = (edit['insert_text_position'][0], points['start'][1])
        node_start = tree_with_completion.root_node.descendant_for_point_range(new_point, new_point)
        if node_start.type == node_language['comment']:
            points['trigger'] = new_point

        while node_start and node_start.parent and node_start.parent.start_point[0] == new_point[0]:
            node_start = node_start.parent
        if node_start.type == node_language['method']:
            points['trigger'] = new_point


    return {
        'insert_text': completion['insert_text'],
        'points': points,
        'tree': tree_with_completion,
    }


def paste_completion(params):
    insert_text = params['completion']['insert_text']
    parser = params['parser']
    document = params['document']
    doc_context = params['doc_context']
    current_line_suffix = doc_context['current_line_suffix']

    injected_completion_text = doc_context.get('injected_completion_text', '')

    matching_suffix_length = get_matching_suffix_length(insert_text, current_line_suffix)

    text_with_completion, edit = splice_insert_text({
        'current_text': document.text,
        'start_index': document.offset,
        'length_removed': matching_suffix_length,
        'insert_text': injected_completion_text + insert_text,
    })

    tree = parser.safe_parse(document.text)
    tree.edit(start_byte=edit['start_byte'],
              old_end_byte=edit['old_end_byte'],
              new_end_byte=edit['new_end_byte'],
              start_point=edit['start_point'],
              old_end_point=edit['start_point'],
              new_end_point=edit['start_point'])

    tree_with_completion = parser.safe_parse(text_with_completion, tree)

    return tree_with_completion, edit['new_end_point'], edit


def splice_insert_text(param):
    current_text = param['current_text']
    insert_text = param['insert_text']
    start_index = param['start_index']
    length_removed = param['length_removed']

    old_end_index = start_index + length_removed
    new_end_index = start_index + len(insert_text)

    start_position = get_extent(current_text[:start_index])
    old_end_position = get_extent(current_text[:old_end_index])
    text_with_completion = current_text[:start_index] + insert_text + current_text[old_end_index:]
    new_end_position = get_extent(text_with_completion[:new_end_index])
    insert_text_position = (start_position[0] + count_leading_newlines(insert_text), start_position[1])

    return text_with_completion, {
        'start_byte': start_index,
        'start_point': start_position,
        'old_end_byte': old_end_index,
        'old_end_point': old_end_position,
        'new_end_byte': new_end_index,
        'new_end_point': new_end_position,
        'insert_text_position': insert_text_position
    }


def get_extent(text: str) -> Tuple[int, int]:
    row = 0
    index = 0
    while index != -1:
        index = text.find('\n', index)
        if index != -1:
            index += 1
            row += 1
    return (row, len(text) - index)


def count_leading_newlines(text: str) -> int:
    count = 0
    for char in text:
        if char == '\n':
            count += 1
        else:
            break
    return count
