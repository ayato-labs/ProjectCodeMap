import tree_sitter_python as ts
from tree_sitter import Language, Parser, Query, QueryCursor

lang = Language(ts.language())
p = Parser(lang)

with open("src/project_code_map/cli.py", "rb") as f:
    content = f.read().decode('utf-8')

tree = p.parse(bytes(content, "utf-8"))

# Test function + decorated only
query_str = """
(
  (function_definition
    name: (identifier) @name
    parameters: (parameters) @params
    body: (_) @body
    (#not-match? @name "^_")
  ) @func
  (decorated_definition
    (function_definition
      name: (identifier) @name
      parameters: (parameters) @params
      body: (_) @body
      (#not-match? @name "^_")
    ) @func
  )
)
"""

q = Query(lang, query_str)
cursor = QueryCursor(q)
captures = cursor.captures(tree.root_node)

print(f"Capture groups: {len(captures)}")
for k, v in captures.items():
    print(f"  {k}: {len(v)} nodes")
    for n in v:
        print(f"    {n.type}: {n.text.decode()[:80]}")