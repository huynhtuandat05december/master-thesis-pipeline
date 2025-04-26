import json
from datetime import datetime
from typing import Tuple, Union, List
import datasets


def get_all_repositories(folder_path, output_file):
    import os

    folders = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]

    with open(output_file, "w") as f:
        for folder in folders:
            json.dump(folder, f)
            f.write("\n")  # Ensure newline for JSONL format

    print(f"Folder names written to {output_file}")

def get_file_line_numbers(base_path: str, file_path: str, code_snippet: str) -> Tuple[int, int, int]:
    """
    Get the start and end line numbers and character offset of the code snippet in the file.
    Returns (context_start_lineno, line_no, char_offset)
    where char_offset is the position at the start of the matching line.
    """
    try:
        # Construct full path from repository root
        full_path = f"{base_path}/{file_path}"
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        # Split both file and snippet into lines
        file_lines = file_content.splitlines()
        snippet_lines = code_snippet.splitlines()
        
        if not snippet_lines:
            return 0, 0, 0
            
        # Get first line of snippet
        first_line = snippet_lines[0].strip()
        last_line = snippet_lines[-1]
        
        # Find the first line in file content
        for i, file_line in enumerate(file_lines):
            if file_line.strip() == first_line:

                # Return 0 as the character offset for the start of the line
                return i, i + len(snippet_lines) - 1, len(last_line)
                
        # If we can't find the match, return 0, 0, 0
        print(f"Could not find match for {file_path}")
        return 0, 0, 0
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return 0, 0, 0

def get_prefix_suffix(base_path: str, file_path: str, code_snippet: str, ground_truth: str) -> Tuple[str, str]:
    """
    Get the prefix and suffix surrounding the code snippet in the file.
    Returns (prefix, suffix) where prefix is the content before the snippet
    and suffix is the content after the snippet.
    """
    try:
        # Construct full path from repository root
        full_path = f"{base_path}/{file_path}"
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Split both file and snippet into lines
        file_lines = file_content.splitlines(True)  # Keep line endings
        snippet_lines = code_snippet.splitlines()
        
        if not snippet_lines:
            print(f"Empty snippet for {file_path}")
            return "", ""
            
        # Get first line of snippet
        first_line = snippet_lines[0].strip()
        
        # Find the first line in file content
        found = False
        prefix_lines = []
        suffix_lines = []
        
        for i, file_line in enumerate(file_lines):
            if not found and file_line.strip() == first_line:
                prefix_lines = file_lines[:i + len(snippet_lines) ]
                #remove the ground truth from the last line of the prefix
                prefix_lines[-1] = prefix_lines[-1].replace(ground_truth, "")
                suffix_end = i + len(snippet_lines) 
                suffix_lines = file_lines[suffix_end:] if suffix_end < len(file_lines) else []
                break
                
        if True:
            prefix = ''.join(prefix_lines)
            suffix = ''.join(suffix_lines)
            return prefix, suffix
        else:
            print(f"Could not find snippet in {file_path}")
            return "", ""
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return "", ""


def convert_dataset_prefix_and_suffix(base_path: str, input_file, output_file):
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        for idx, line in enumerate(infile):
            data = json.loads(line)

            prefix, suffix = get_prefix_suffix(base_path, data["fpath"], data["input"], data["gt"])
            context_start, completion_line, char_offset = get_file_line_numbers(
                base_path,
                data["fpath"],
                data["input"]
            )

            list_path = data["fpath"].split("/")

            new_data = {
                **data,
                "prefix": prefix,
                "suffix": suffix,
                "metadata": {
                    "task_id": f'{list_path[0]}/{idx}',
                    "fpath_tuple": list_path,
                    "context_start_lineno": context_start,
                    "line_no": completion_line,
                    "context_start_characterno": char_offset
                }
            }
            outfile.write(json.dumps(new_data) + "\n")


def load_dataset(task: Union[str, List[str]] = ["block", "control", "api"]):
    """
    Load dataset samples for one or multiple tasks.
    
    Args:
        task: Either a single task name (str) or a list of task names (List[str])
              Valid tasks are 'block', 'control', 'api', and 'block_v2'
    
    Returns:
        A list of dataset samples
    """
    if isinstance(task, str):
        # Single task case (original behavior)
        ds = datasets.load_dataset("gonglinyuan/safim", task, split="test")
        lst = []
        for m in ds:
            m["unit_tests"] = json.loads(m["unit_tests"])
            lst.append(m)
        return lst
    elif isinstance(task, list):
        # Multitask case - load multiple tasks and combine them
        lst = []
        for t in task:
            ds = datasets.load_dataset("gonglinyuan/safim", t, split="test")
            for m in ds:
                m["unit_tests"] = json.loads(m["unit_tests"])
                lst.append(m)
        return lst
    else:
        raise TypeError("Task must be either a string or a list of strings")

if __name__ == '__main__':
    # get_all_repositories()
    base_path = "/Users/datht22/Desktop/codevista/jaccard_warp/ReccEval/Source_Code"
    input_file = "/Users/datht22/Desktop/codevista/jaccard_warp/ReccEval/metadata.jsonl"
    output_file = "/Users/datht22/Desktop/codevista/jaccard_warp/dataset/metadata.jsonl"
    convert_dataset_prefix_and_suffix(base_path, input_file, output_file)