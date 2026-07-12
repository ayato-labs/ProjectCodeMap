import tree_sitter_php as tsphp
from tree_sitter import Language, Parser

lang = Language(tsphp.language_php())
parser = Parser(lang)
code = b'<?php function foo() {} class Bar { public function baz() {} }'
tree = parser.parse(code)
print(tree.root_node.sexp())