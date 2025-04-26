from abc import abstractmethod, ABC


class FIMModelSpecificPromptExtractor(ABC):
    @abstractmethod
    def get_context_prompt(self, filename: str, content: str):
        pass

    def file_snippet_to_prompt_string(self, snippet):
        # empty function
        pass

    @abstractmethod
    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        pass


class StarcoderPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)


    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"<fim_prefix>{intro}{prefix}<fim_suffix>{suffix}<fim_middle>"


class CodeQwenPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"{intro}\n<file_sep>{filename}\n<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle> "  #don't remove last space. Qwen sometimes add a space in the first of completion. Don't sure fixed by last space in prompt.


class CodeQwen25PromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)

    def file_snippet_to_prompt_string(self, snippet):
        return f"<|file_sep|>{snippet['uri']}\n{snippet['content']}"

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"{intro}\n<|file_sep|>{filename}\n<|fim_prefix|>{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"


class CodeLlamaPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"<PRE> {intro}{prefix} <SUF>{suffix} <MID>"


class CodeGemmaPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"<|fim_prefix|>{intro}{prefix}<|fim_suffix|>{suffix}<|fim_middle|>"


class DeepSeekPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return f"#{filename}\n{content}"

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        # Deepseek paper: https://arxiv.org/pdf/2401.14196
        return f"{intro}\n#{filename}\n<｜fim▁begin｜>{prefix}<｜fim▁hole｜>{suffix}<｜fim▁end｜>"


class DefaultModelPromptExtractor(FIMModelSpecificPromptExtractor):
    def get_context_prompt(self, filename: str, content: str):
        return get_default_context_prompt(filename, content)

    def get_infilling_prompt(self, filename: str, intro: str, prefix: str, suffix: str):
        return f"{intro}{prefix}"


def get_default_context_prompt(filename: str, content: str):
    return f"Here is a reference snippet of code from {filename}:\n\n{content}"
