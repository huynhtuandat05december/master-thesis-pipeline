from .utils import remove_trailing_whitespace, trim_until_suffix, collapse_duplicative_whitespace


def get_matching_suffix_length(insert_text, current_line_suffix):
    j = 0
    for i in range(len(insert_text)):
        if j >= len(current_line_suffix):
            return j
        if insert_text[i] == current_line_suffix[j]:
            j += 1
    return j


def process_completion(completion, params, multiline):
    document = params['document']
    insert_text = completion['insert_text']
    doc_context = params['doc_context']

    prefix = doc_context['prefix']
    suffix = doc_context['suffix']

    if len(insert_text) == 0:
        return completion

    if len(insert_text) == 0:
        return completion

    if multiline:
        insert_text = remove_trailing_whitespace(insert_text)
    # else:
    #     new_line_index = insert_text.find('\n')
    #     if new_line_index != -1:
    #         insert_text = insert_text[:new_line_index + 1]

    insert_text = trim_until_suffix(insert_text, prefix, suffix, document.language_id)
    insert_text = collapse_duplicative_whitespace(prefix, insert_text)
    insert_text = insert_text.rstrip()

    return {**completion, 'insert_text': insert_text}
