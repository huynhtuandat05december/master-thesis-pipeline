from .detect_multiline import detect_multiline
from schema.common import Position, Document
from post_processing.process_inline_completion import get_matching_suffix_length
from post_processing.utils import get_last_line, get_first_line, get_next_non_empty_line, get_prev_non_empty_line, get_position_after_text_insertion

def get_current_doc_context(document, language_id):
    prefix = document.prefix
    suffix = document.suffix

    doc_context = get_derived_doc_context({
        'language_id': language_id,
        'position': Position(line=document.position.line, character=document.position.character),
        'document_dependent_context': {
            'prefix': prefix,
            'suffix': suffix,
        },
    })

    return doc_context


def get_lines_context(prefix, suffix):
    current_line_prefix = get_last_line(prefix)
    current_line_suffix = get_first_line(suffix)

    prev_non_empty_line = get_prev_non_empty_line(prefix)
    next_non_empty_line = get_next_non_empty_line(suffix)

    return {
        'current_line_prefix': current_line_prefix,
        'current_line_suffix': current_line_suffix,
        'prev_non_empty_line': prev_non_empty_line,
        'next_non_empty_line': next_non_empty_line,
    }


def insert_into_doc_context(params):
    insert_text = params.insert_text
    language_id = params.language_id
    doc_context = params.doc_context

    updated_position = get_position_after_text_insertion(doc_context.position, insert_text)

    updated_doc_context = get_derived_doc_context({
        'language_id': language_id,
        'position': updated_position,
        'document_dependent_context': {
            'prefix': doc_context.prefix + insert_text,
            'suffix': doc_context.suffix[get_matching_suffix_length(insert_text, doc_context.current_line_suffix):],
        },
    })

    return updated_doc_context


def get_derived_doc_context(params):
    position = params['position']
    document_dependent_context = params['document_dependent_context']
    language_id = params['language_id']

    lines_context = get_lines_context(document_dependent_context['prefix'], document_dependent_context['suffix'])

    multiline_info = detect_multiline({
        'doc_context': {**document_dependent_context, **lines_context},
        'language_id': language_id,
        'position': position,
    })

    return {
        **document_dependent_context,
        **lines_context,
        'position': position,
        'multiline_trigger': multiline_info.get('multiline_trigger'),
        'multiline_trigger_position': multiline_info.get('multiline_trigger_position'),
    }


if __name__ == "__main__":

    document = Document(uri="/Users/datht22/Desktop/codevista/jaccard_warp/test/test.py", language_id="python", text="""
from .import_test import another_call
def example():
    print("Hello")
    another_call()
def another_call2():
    """.strip(),
        complete_prefix="""
from .import_test import another_call
def example():
    print("Hello")
    another_call()
def another_call2():
    """.strip(),
        complete_suffix="""    """.strip(),
        position=Position(line=5, character=4)
    )
    print(get_current_doc_context(document, 'python'))