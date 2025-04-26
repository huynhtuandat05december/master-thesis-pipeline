from context_mixer import ContextMixer
from schema.common import Document, Position
import asyncio
import os
import json
import jsonlines
from tqdm import tqdm
import argparse
from prompt.fim_utils import CodeQwen25PromptExtractor

context_mixer = ContextMixer()
prompt_extractor = CodeQwen25PromptExtractor()

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

    repo = data["metadata"]["fpath_tuple"][0]
    contexts = asyncio.run(context_mixer.get_context(document, document.position, repo))

    intro = ''
    context_dict = []

    for context in contexts['context']:
        context_dict.append(context.to_dict())
        snippet = prompt_extractor.file_snippet_to_prompt_string({'uri': context.uri, 'content': context.content})
        intro += f'{snippet}\n'

    prompt = prompt_extractor.get_infilling_prompt(data["metadata"]["fpath_tuple"][-1], intro, data["prefix"], data["suffix"])

    return {**data, 'prompt': prompt, 'contexts': context_dict}



def process_jsonl_file(base_dir, input_file, output_file):
    results = []
    
    # Read input JSONL file
    with jsonlines.open(input_file) as reader:
        # Wrap with tqdm for progress bar
        for data in tqdm(reader, desc="Processing data"):
            try:
                result = process_single_data(base_dir, data)
                results.append(result)
            except Exception as e:
                print(f"Error processing data: {e}")
                # Add the original data with error information
                results.append({"error": str(e), "original": data})
    
    # Write results to output JSONL file
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(results)
    
    print(f"Processed {len(results)} items. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process JSONL file to generate prompts with context')
    parser.add_argument('--base_dir', type=str, required=True, 
                        help='Base directory containing source code files')
    parser.add_argument('--input', type=str, required=True,
                        help='Input JSONL file path')
    parser.add_argument('--output', type=str, required=True,
                        help='Output JSONL file path')
    
    args = parser.parse_args()
    
    process_jsonl_file(args.base_dir, args.input, args.output)
    
    