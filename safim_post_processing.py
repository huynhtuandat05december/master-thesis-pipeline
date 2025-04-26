from schema.common import Document, Position
import os
import jsonlines
from tqdm import tqdm
from post_processing.main import parse_and_truncate_completion, process_completion
from context.handle_current_context import get_current_doc_context
from process_data import load_dataset
def process_single_data(data):


    document = Document(
        uri='', 
        language_id=data["language_id"], 
        text=data["prefix"] + data["suffix"], 
        prefix=data["prefix"], 
        suffix=data["suffix"], 
        offset=len(data["prefix"]), 
        position=Position(line=data["metadata"]["line_no"], character=data["metadata"]["context_start_characterno"])
    )

    doc_context = get_current_doc_context(document, data["language_id"])

    raw_completion = data["completion"]

    completion = parse_and_truncate_completion(raw_completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    if completion is None:
        return {
            **data,
            'completion': raw_completion
        }

    completed_completion = process_completion(completion, {
        'document': document,
        'doc_context': doc_context,
    }, True)

    return {
        **data,
        'completion': completed_completion['insert_text']
    }


COMPLETION_PLACEHOLDER = {
    "python": "{{completion}}",
    "java": "{{completion}}",
    "cpp": "{{completion}}",
    "csharp": "{{completion}}",
}
def get_infilling_parts(sample):
    parts = sample["eval_prompt"].split(COMPLETION_PLACEHOLDER[sample["lang"]])
    assert len(parts) == 2
    return parts

def process_jsonl_file(input_file, output_file):
    results = []

    dataset = load_dataset(['api', 'control', 'block'])
    # Read input JSONL file
    with jsonlines.open(input_file) as reader:
        # Wrap with tqdm for progress bar
        for index, data in enumerate(tqdm(reader, desc="Processing data")):
            # prefix, suffix = get_infilling_parts(dataset[index])
            # new_data = {
            #     "language_id": dataset[index]["lang"],
            #     "metadata": {
            #         "line_no": len(prefix.split("\n")) - 1,
            #         "context_start_characterno": len(prefix.split("\n")[-1]) -1
            #     },
            #     "prefix": prefix,
            #     "suffix": suffix,
            #     **data
            # }
            # result = process_single_data(new_data)
            # results.append(result)
            try:
                prefix, suffix = get_infilling_parts(dataset[index])
                new_data = {
                    "language_id": dataset[index]["lang"],
                    "metadata": {
                        "line_no": len(prefix.split("\n")) - 1,
                        "context_start_characterno": len(prefix.split("\n")[-1]) -1
                    },
                    "prefix": prefix,
                    "suffix": suffix,
                    **data,
                }
                result = process_single_data(new_data)
                results.append(result)
            except Exception as e:
                print(f"Error processing data: {index}: {e}")
                # Add the original data with error information
                results.append({"error": str(e), **data})
        
    # Write results to output JSONL file
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(results)
    
    print(f"Processed {len(results)} items. Results saved to {output_file}")

if __name__ == "__main__":

    base_dir   = '/Users/datht22/Desktop/codevista/jaccard_warp/ReccEval/Source_Code/'

    input= '/Users/datht22/Desktop/codevista/jaccard_warp/result//qwen-safim-infillng.jsonl'
    output= '/Users/datht22/Desktop/codevista/jaccard_warp/result/qwen-safim-infillng-post_processed.jsonl'
    
    process_jsonl_file(input, output)
    
    