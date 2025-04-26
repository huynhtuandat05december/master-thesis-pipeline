go_keywords = {
    "break", "case", "chan", "const", "continue", "default", "defer", "else", "fallthrough", "for",
    "func", "go", "goto", "if", "import", "interface", "map", "package", "range", "return", "select",
    "struct", "switch", "type", "var",
    # Common variables, types we don't need to follow
    "Context", "ctx", "err", "error", "ok"
}

typescript_keywords = {
    "any", "as", "async", "boolean", "break", "case", "catch", "class", "const", "constructor", "continue",
    "debugger", "declare", "default", "delete", "do", "else", "enum", "export", "extends", "false", "finally",
    "for", "from", "function", "if", "implements", "import", "in", "instanceof", "interface", "let", "module",
    "new", "null", "number", "of", "package", "private", "protected", "public", "require", "return", "static",
    "string", "super", "switch", "symbol", "this", "throw", "true", "try", "type", "typeof", "var", "void",
    "while", "with", "yield"
}

python_keywords = {
    "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else",
    "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None",
    "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"
}

common_keywords = go_keywords | typescript_keywords | python_keywords

common_import_paths = {
    # The TS lib folder contains the TS standard library and all of ECMAScript.
    "node_modules/typescript/lib",
    # The node library contains the standard node library.
    "node_modules/@types/node",
    # All CSS properties as TS types.
    "node_modules/csstype",
    # Common React type definitions.
    "node_modules/@types/prop-types",
    "node_modules/@types/react/",
    "node_modules/next/",
    # Go stdlib installation (covers Brew installs at a minimum)
    "libexec/src/",
    # Python stdlib
    "lib/python3.",
    "stdlib/builtins.pyi",
}
