from typing import List, Dict, Tuple
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from collections import defaultdict
from nltk.stem import PorterStemmer
import nltk
from schema.jaccard import JaccardMatch
nltk.download('stopwords')
nltk.download('punkt_tab')

# Initialize stemmer and tokenizer (if nltk is used)
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))


def best_jaccard_matches(target_text: str, match_text: str, window_size: int, max_matches: int, slide: int = 2) -> List[JaccardMatch]:
    if window_size < 1:
        raise ValueError("window_size must be a positive integer")

    target_occurrences = get_word_occurrences(target_text)
    target_word_counts = sum_word_counts(target_occurrences)
    
    lines = match_text.split('\n')
    words_for_each_line = [get_word_occurrences(line) for line in lines]

    first_window_end = min(window_size - 1, len(lines) - 1)
    window_occurrences = defaultdict(int)
    
    for i in range(first_window_end + 1):
        for word, count in words_for_each_line[i].items():
            window_occurrences[word] += count
    
    window_word_counts = sum_word_counts(window_occurrences)

    intersection_occurrences = {
        word: min(count, window_occurrences.get(word, 0)) for word, count in target_occurrences.items()
    }
    intersection_word_counts = sum_word_counts(intersection_occurrences)

    windows = [
        JaccardMatch(
            score=jaccard_similarity(target_word_counts, window_word_counts, intersection_word_counts),
            content="\n".join(lines[:first_window_end + 1]),
            start_line=0,
            end_line=first_window_end
        )
    ]

    # for i in range(1, len(lines) - window_size + 1):
    #     print(i)
    #     window_word_counts += subtract(window_occurrences, words_for_each_line[i - 1])
    #     intersection_word_counts += subtract(intersection_occurrences, words_for_each_line[i - 1])
        
    #     window_increase, intersection_increase = add(
    #         target_occurrences, window_occurrences, intersection_occurrences, words_for_each_line[i + window_size - 1]
    #     )
        
    #     window_word_counts += window_increase
    #     intersection_word_counts += intersection_increase

    #     if lines[i].strip() == "" and i < len(lines) - window_size:
    #         continue

    #     score = jaccard_similarity(target_word_counts, window_word_counts, intersection_word_counts)
    #     start_line = i
    #     end_line = i + window_size - 1

    #     windows.append(JaccardMatch(
    #         score=score,
    #         content="\n".join(lines[start_line:end_line + 1]),
    #         start_line=start_line,
    #         end_line=end_line
    #     ))

    for i in range(slide, len(lines) - window_size + 1, slide):
        window_word_counts += subtract(window_occurrences, words_for_each_line[i - slide])
        intersection_word_counts += subtract(intersection_occurrences, words_for_each_line[i - slide])


        for j in range(slide):
            window_increase, intersection_increase = add(
                target_occurrences, window_occurrences, intersection_occurrences, words_for_each_line[i + window_size - 1 - j]
            )
            
            window_word_counts += window_increase
            intersection_word_counts += intersection_increase

        if lines[i].strip() == "" and i < len(lines) - window_size:
            continue

        score = jaccard_similarity(target_word_counts, window_word_counts, intersection_word_counts)
        start_line = i
        end_line = i + window_size - 1

        windows.append(JaccardMatch(
            score=score,
            content="\n".join(lines[start_line:end_line + 1]),
            start_line=start_line,
            end_line=end_line
        ))

    windows.sort(key=lambda x: x.score, reverse=True)
    retained_windows = []
    included_lines = set()

    for window in windows:
        if not any(i in included_lines for i in range(window.start_line, window.end_line + 1)):
            included_lines.update(range(window.start_line, window.end_line + 1))
            retained_windows.append(window)

    return retained_windows[:max_matches]

def jaccard_similarity(left: int, right: int, intersection: int) -> float:
    union = left + right - intersection
    if union <= 0:
        return 0
    return intersection / union

def get_word_occurrences(s: str) -> Dict[str, int]:
    frequency_counter = defaultdict(int)
    words = word_tokenize(s)
    
    # Break compound words and filter out stopwords
    filtered_words = [
        word.lower() 
        for w in words 
        for word in break_camel_and_snake_case(w)
        if word.lower() not in stop_words
    ]
    
    # Apply stemming and count occurrences
    for word in filtered_words:
        stemmed_word = stemmer.stem(word)
        frequency_counter[stemmed_word] += 1
        
    return frequency_counter

def sum_word_counts(words: Dict[str, int]) -> int:
    return sum(words.values())

def subtract(minuend: Dict[str, int], subtrahend: Dict[str, int]) -> int:
    decrease = 0
    for word, count in subtrahend.items():
        current_count = minuend.get(word, 0)
        new_count = max(0, current_count - count)
        decrease += new_count - current_count
        minuend[word] = new_count
    return decrease

def add(target: Dict[str, int], window: Dict[str, int], intersection: Dict[str, int], new_line: Dict[str, int]) -> Tuple[int, int]:
    window_increase = 0
    intersection_increase = 0
    
    for word, count in new_line.items():
        window_increase += count
        window[word] += count
        
        if target.get(word, 0) > 0:
            new_intersection_count = min(count + intersection.get(word, 0), target[word])
            intersection_increase += new_intersection_count - intersection.get(word, 0)
            intersection[word] = new_intersection_count
            
    return window_increase, intersection_increase

def break_camel_and_snake_case(word: str) -> List[str]:
    camel_case_regex = re.compile(r'([a-z])([A-Z])')
    snake_case_regex = re.compile(r'_')
    
    # Break camelCase words
    broken_word = camel_case_regex.sub(r'\1 \2', word)
    # Break snake_case words
    broken_word = snake_case_regex.sub(' ', broken_word)
    
    # If no changes, return original word
    if broken_word == word:
        return [word]
    
    word_parts = broken_word.split()
    word_parts.append(word)  # Add original word for exact matches
    return word_parts
