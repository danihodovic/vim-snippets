import ast
from collections import namedtuple

import vim

def bypass_ultisnips_error(func):
    def wrapper(*args, **kwargs):
        snip = args[0]
        result = func(*args, **kwargs)
        snip.buffer._change_tick = int(vim.eval("b:changedtick"))
        return result

    return wrapper

def normalized_imports(contents):
    root = ast.parse(contents)
    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Import):
            for n in node.names:
                yield n.name
        elif isinstance(node, ast.ImportFrom):
            module_path = node.module
            for n in node.names:
                yield ".".join([node.module, n.name])

def normalized_import_line(line):
    try:
        return next(normalized_imports(line), None)
    except SyntaxError:
        # We may encounter a syntax error because of lines like class Foo:
        # which are technically incomplete python
        pass

@bypass_ultisnips_error
def clean_imports(snip):
    buffer = vim.current.buffer
    snip_start_line, _ = snip.snippet_start
    snip_end_line, _ = snip.snippet_end
    snippet_contents = "\n".join(snip.buffer[snip_start_line:snip_end_line+1])
    contents_before_snippet = "\n".join(buffer[0:snip_start_line])

    snippet_imports = set(normalized_imports(snippet_contents))
    file_imports = set(normalized_imports(contents_before_snippet))
    missing_imports = snippet_imports.difference(file_imports)

    imports_to_add = []
    for line in buffer[snip_start_line:snip_end_line]:
        if normalized_import_line(line) in missing_imports:
            imports_to_add.append(line)

    # Delete snippet imports
    i = snip_start_line
    while i <= snip_end_line:
        if normalized_import_line(buffer[i]):
            buffer[i] = None
            i -= 1
            snip_end_line -= 1
        i += 1

    # Add missing imports to top
    for import_line in imports_to_add:
        buffer.append(import_line, index=0)

    snip.cursor.preserve()
