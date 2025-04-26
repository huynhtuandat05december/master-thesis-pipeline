from schema.common import Position
from .parse_completion import parse_completion
from .truncate_parsed_completion import truncate_parsed_completion


def parse_and_truncate_completion(completion: str, params, multiline: bool):
    document = params['document']
    doc_context = params['doc_context']

    insert_text_before_truncation = completion.rstrip()

    parsed = parse_completion({
        'completion': {'insert_text': insert_text_before_truncation},
        'document': document,
        'doc_context': doc_context,
    })

    if parsed['insert_text'] == '':
        return parsed

    if multiline:
        truncation_result = truncate_multiline_block({
            'parsed': parsed,
            'document': document,
            'doc_context': doc_context,
        })

        parsed['insert_text'] = truncation_result['insert_text']

    return parsed


def truncate_multiline_block(params):
    parsed = params['parsed']
    doc_context = params['doc_context']
    document = params['document']

    return {
        **truncate_parsed_completion({
            'completion': parsed,
            'doc_context': doc_context,
            'document': document,
        }),
    }

