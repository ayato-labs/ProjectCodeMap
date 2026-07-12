import tree_sitter_python as ts
from tree_sitter import Language, Parser, Query, QueryCursor

from src.project_code_map.parser.python import _PY_LANGUAGE, _PY_QUERY, _PY_PARSER, _PY_QUERY_OBJ
from src.project_code_map.config import Config

config = Config()

with open("src/project_code_map/cli.py", "r", encoding="utf-8") as f:
    content = f.read()

tree = _PY_PARSER.parse(bytes(content, "utf-8"))
cursor = QueryCursor(_PY_QUERY_OBJ)
captures = cursor.captures(tree.root_node)

print(f"Capture groups: {len(captures)}")
for capture_name, nodes in captures.items():
    print(f"  {capture_name}: {len(nodes)} nodes")
    for n in nodes:
        print(f"    type={n.type}, line={n.start_point[0]}")

# Now test the sorting logic
all_nodes = []
for capture_name, nodes in captures.items():
    for node in nodes:
        all_nodes.append((node.start_point[0], node, capture_name))

all_nodes.sort(key=lambda x: x[0])

print("\nSorted nodes:")
for line, node, capture_name in all_nodes:
    print(f"  Line {line}: {capture_name} -> {node.type} ({node.text.decode()[:80] if node.text else ''})")