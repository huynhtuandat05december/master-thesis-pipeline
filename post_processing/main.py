from post_processing.parse_and_truncate_completion import parse_and_truncate_completion
from post_processing.process_inline_completion import process_completion
from context.handle_current_context import get_current_doc_context
from schema.common import Document, Position

def main():

    prefix = """from .import_test import another_call
def example():
    print("Hello")
    another_call()
def another_call2():
    """

    suffix = """"""

    document = Document(uri="/Users/datht22/Desktop/codevista/jaccard_warp/test/test.py", language_id="python", text=prefix + suffix,
        prefix=prefix,
        offset=len(prefix),
        suffix=suffix,
        position=Position(line=5, character=4)
    )
    doc_context = get_current_doc_context(document, 'python')

    print(doc_context)


    raw_completion = """print("Hello2")
    another_call()
def another_call3():
    print("Hello3")"""

    completion = parse_and_truncate_completion(raw_completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    if completion is None:
        print("Error")
        return {
            'insert_text': '',
            'stop_reason': 'error'
        }

    completed_completion = process_completion(completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    print(completed_completion)

if __name__ == "__main__":
    main()