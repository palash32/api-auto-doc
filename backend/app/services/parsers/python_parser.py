import logging
from typing import List, Dict, Any, Optional
from tree_sitter import Language, Parser
import tree_sitter_python

logger = logging.getLogger(__name__)

class PythonParser:
    """
    Parser for Python files using tree-sitter.
    Extracts metadata relevant for API documentation.
    """
    
    def __init__(self):
        self.PY_LANGUAGE = Language(tree_sitter_python.language(), "python")
        self.parser = Parser()
        self.parser.set_language(self.PY_LANGUAGE)
        
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse Python content and return metadata.
        """
        try:
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            return {
                "functions": self._extract_functions(root_node, content),
                "classes": self._extract_classes(root_node, content),
                "imports": self._extract_imports(root_node, content)
            }
        except Exception as e:
            logger.error(f"Error parsing Python content: {e}")
            return {"error": str(e)}

    def _extract_functions(self, node, content: str) -> List[Dict[str, Any]]:
        functions = []
        
        # Query for function definitions
        query = self.PY_LANGUAGE.query("""
        (function_definition
            name: (identifier) @function.name
            parameters: (parameters) @function.params
        ) @function.def
        """)
        
        captures = query.captures(node)
        
        # Process captures (simplified for MVP)
        # Tree-sitter returns list of (Node, str) tuples
        # We need to group them by function definition
        
        # Alternative: Walk the tree manually for more control
        for child in node.children:
            if child.type == "function_definition":
                func_name = child.child_by_field_name("name").text.decode("utf8")
                params = child.child_by_field_name("parameters").text.decode("utf8")
                
                # Get docstring
                docstring = self._get_docstring(child)
                
                # Get decorators
                decorators = self._get_decorators(child)
                
                functions.append({
                    "name": func_name,
                    "params": params,
                    "docstring": docstring,
                    "decorators": decorators,
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1
                })
                
            # Recurse for nested functions or methods inside classes
            if child.type == "class_definition":
                # We handle class methods in _extract_classes, but if we wanted flat list:
                # functions.extend(self._extract_functions(child.body, content))
                pass
                
        return functions

    def _extract_classes(self, node, content: str) -> List[Dict[str, Any]]:
        classes = []
        for child in node.children:
            if child.type == "class_definition":
                class_name = child.child_by_field_name("name").text.decode("utf8")
                docstring = self._get_docstring(child)
                
                # Extract methods
                body = child.child_by_field_name("body")
                methods = self._extract_functions(body, content)
                
                classes.append({
                    "name": class_name,
                    "docstring": docstring,
                    "methods": methods,
                    "start_line": child.start_point[0] + 1,
                    "end_line": child.end_point[0] + 1
                })
        return classes

    def _extract_imports(self, node, content: str) -> List[str]:
        imports = []
        for child in node.children:
            if child.type in ["import_statement", "import_from_statement"]:
                imports.append(child.text.decode("utf8"))
        return imports

    def _get_docstring(self, node) -> Optional[str]:
        """Extract docstring from function or class node."""
        body = node.child_by_field_name("body")
        if body and body.children:
            first_child = body.children[0]
            if first_child.type == "expression_statement":
                expression = first_child.children[0]
                if expression.type == "string":
                    # Remove quotes
                    text = expression.text.decode("utf8")
                    return text.strip('"""').strip("'''").strip('"').strip("'")
        return None

    def _get_decorators(self, node) -> List[str]:
        """Extract decorators for a function."""
        decorators = []
        # Decorators appear as siblings before the function_definition in the AST?
        # No, in tree-sitter-python, decorated_definition wraps the function
        
        parent = node.parent
        if parent.type == "decorated_definition":
            for child in parent.children:
                if child.type == "decorator":
                    decorators.append(child.text.decode("utf8").strip())
        return decorators
