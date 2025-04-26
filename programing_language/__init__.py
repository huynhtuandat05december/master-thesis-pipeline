import re


class ProgrammingLanguage:
    ASTRO = "astro"
    C = "c"
    CPP = "cpp"
    C_SHARP = "c_sharp"
    DART = "dart"
    GO = "go"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    JAVASCRIPTREACT = "javascriptreact"
    KOTLIN = "kotlin"
    PHP = "php"
    RUST = "rust"
    SVELTE = "svelte"
    TYPESCRIPT = "typescript"
    TYPESCRIPTREACT = "typescriptreact"
    VUE = "vue"
    PYTHON = "python"
    ELIXIR = "elixir"
    OBJECTIVE_C = "objective-c"
    CSS = "css"
    ELISP = 'elisp'
    ELM = 'elm'
    HTML = 'html'
    JSON = 'json'
    LUA = 'lua'
    OCAML = 'ocaml'
    RESCRIPT = 'rescript'
    RUBY = 'ruby'
    SCALA = 'scala'
    BASH = 'bash'
    SWIFT = 'swift'

NODE_LANGUAGE = {
    ProgrammingLanguage.OBJECTIVE_C: None,
    ProgrammingLanguage.C: {
        "comment": "comment",
        "method": "function_definition",
        "function": "function_definition"
    },
    ProgrammingLanguage.CPP: {
        "comment": "comment",
        "method": "function_definition",
        "function": "function_definition"
    },
    ProgrammingLanguage.C_SHARP: {
        "comment": "comment",
        "method": "method_declaration"
    },
    ProgrammingLanguage.CSS: None,
    ProgrammingLanguage.DART: None,
    ProgrammingLanguage.ELISP: None,
    ProgrammingLanguage.ELIXIR: None,
    ProgrammingLanguage.ELM: None,
    ProgrammingLanguage.GO: None,
    ProgrammingLanguage.HTML: None,
    ProgrammingLanguage.JAVA: {
        "comment": "line_comment",
        "method": "method_declaration"
    },
    ProgrammingLanguage.JAVASCRIPT: {
        "comment": "comment",
        "method": "method_definition",
        "function": "function_declaration"
    },
    ProgrammingLanguage.JAVASCRIPTREACT: {
        "comment": "comment",
        "method": "function_definition",
        "function": "function_declaration"
    },
    ProgrammingLanguage.JSON: None,
    ProgrammingLanguage.KOTLIN: {
        "comment": "line_comment",
        "method": "function_declaration",
        "function": "function_declaration"
    },
    ProgrammingLanguage.LUA: None,
    ProgrammingLanguage.OCAML: None,
    ProgrammingLanguage.PHP: {
        "comment": "comment",
        "method": "method_declaration",
        "function": "function_definition"
    },
    ProgrammingLanguage.PYTHON: {
        "comment": "comment",
        "method": "function_definition",
        "function": "function_definition"
    },
    ProgrammingLanguage.RESCRIPT: None,
    ProgrammingLanguage.RUBY: {
        "comment": "comment",
        "method": "method"
    },
    ProgrammingLanguage.RUST: None,
    ProgrammingLanguage.SCALA: None,
    ProgrammingLanguage.BASH: None,
    ProgrammingLanguage.SWIFT: None,
    ProgrammingLanguage.TYPESCRIPT: {
        "comment": "comment",
        "method": "method_definition",
        "function": "function_declaration"
    },
    ProgrammingLanguage.TYPESCRIPTREACT: {
        "comment": "comment",
        "method": "method_definition",
        "function": "function_declaration"
    },
}


def get_language_config(language_id):
    common_languages = [
        ProgrammingLanguage.ASTRO,
        ProgrammingLanguage.C,
        ProgrammingLanguage.CPP,
        ProgrammingLanguage.C_SHARP,
        ProgrammingLanguage.DART,
        ProgrammingLanguage.GO,
        ProgrammingLanguage.JAVA,
        ProgrammingLanguage.JAVASCRIPT,
        ProgrammingLanguage.JAVASCRIPTREACT,
        ProgrammingLanguage.KOTLIN,
        ProgrammingLanguage.PHP,
        ProgrammingLanguage.RUST,
        ProgrammingLanguage.SVELTE,
        ProgrammingLanguage.TYPESCRIPT,
        ProgrammingLanguage.TYPESCRIPTREACT,
        ProgrammingLanguage.VUE,
        ProgrammingLanguage.PYTHON,
        ProgrammingLanguage.ELIXIR
    ]

    if not (language_id in common_languages):
        return None

    if language_id == ProgrammingLanguage.PYTHON:
        return {
            'block_start': ':',
            'block_else_test': re.compile(r'^[\t ]*(elif |else:)'),
            'block_end': None,
            'comment_start': '# '
        }

    if language_id == ProgrammingLanguage.ELIXIR:
        return {
            'block_start': 'do',
            'block_else_test': re.compile(r'^[\t ]*(else|else do)'),
            'block_end': 'end',
            'comment_start': '# '
        }

    return {
        'block_start': '{',
        'block_else_test': re.compile(r'^[\t ]*} else'),
        'block_end': '}',
        'comment_start': '// '
    }
