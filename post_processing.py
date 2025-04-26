from schema.common import Document, Position
import os
import jsonlines
from tqdm import tqdm
import argparse
from post_processing.main import parse_and_truncate_completion, process_completion
from context.handle_current_context import get_current_doc_context

def process_single_data(base_dir, data):

    language_id = "python"

    document = Document(
        uri=base_dir +  os.path.join(*data["metadata"]["fpath_tuple"]), 
        language_id=language_id, 
        text=data["prefix"] + data["suffix"], 
        prefix=data["prefix"], 
        suffix=data["suffix"], 
        offset=len(data["prefix"]), 
        position=Position(line=data["metadata"]["line_no"], character=data["metadata"]["context_start_characterno"])
    )

    doc_context = get_current_doc_context(document, language_id)

    raw_completion = data["choices"][0]["text"]

    completion = parse_and_truncate_completion(raw_completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    if completion is None:
        return {
            **data,
            'choices': [{"text":raw_completion}]
        }

    completed_completion = process_completion(completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    return {
        **data,
        'choices': [{"text":completed_completion['insert_text']}]
    }


 
def process_jsonl_file(base_dir, input_file, output_file):
    results = []

    dataset = []
    with jsonlines.open(input_file) as reader:
        for data in reader:
            dataset.append(data)
    
    # Read input JSONL file
    with jsonlines.open(input_file) as reader:
        # Wrap with tqdm for progress bar
        for index, data in enumerate(tqdm(reader, desc="Processing data")):
            try:
                new_data = {
                    **data,
                    'prefix': dataset[index]['prefix'],
                    'suffix': dataset[index]['suffix'],
                }
                result = process_single_data(base_dir, new_data)
                results.append(result)
            except Exception as e:
                print(f"Error processing data: {e}")
                # Add the original data with error information
                results.append({"error": str(e), **data})
    
    # Write results to output JSONL file
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(results)
    
    print(f"Processed {len(results)} items. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Post-process model completions with context')
    parser.add_argument('--base_dir', type=str, required=True,
                        help='Base directory containing source code files')
    parser.add_argument('--input', type=str, required=True,
                        help='Input JSONL file with model completions')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSONL file path for processed completions')
    
    args = parser.parse_args()
    
    process_jsonl_file(args.base_dir, args.input, args.output)
    
    