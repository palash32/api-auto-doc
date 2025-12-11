"""Repository scanner for analyzing source code files."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class RepositoryScanner:
    """Service for scanning repository files and structure."""

    # Files and directories to ignore
    IGNORED_DIRS = {
        ".git", ".github", ".vscode", ".idea", "__pycache__", "node_modules", 
        "venv", "env", "dist", "build", "coverage", "target", "bin", "obj"
    }
    
    IGNORED_EXTENSIONS = {
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
        # Documents
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        # Archives
        ".zip", ".tar", ".gz", ".rar", ".7z",
        # Binary/System
        ".exe", ".dll", ".so", ".dylib", ".class", ".pyc", ".o",
        # Lock files
        ".lock", "package-lock.json", "yarn.lock", "poetry.lock", "Cargo.lock"
    }

    # Language mapping by extension
    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".sh": "shell",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".md": "markdown"
    }

    def scan_repository(self, repo_path: Path) -> List[Dict[str, str]]:
        """
        Scan a repository for relevant source files.
        """
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
            
        results = []
        
        # Initialize parsers (optional - some may fail due to tree_sitter version issues)
        py_parser = None
        try:
            from app.services.parsers.python_parser import PythonParser
            py_parser = PythonParser()
        except Exception as e:
            logger.warning(f"Could not initialize Python parser (tree_sitter issue?): {e}")
        
        for root, dirs, files in os.walk(repo_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS and not d.startswith(".")]
            
            for file in files:
                if file.startswith("."):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(repo_path)
                extension = file_path.suffix.lower()
                
                if extension in self.IGNORED_EXTENSIONS:
                    continue
                
                # Identify language
                language = self.LANGUAGE_MAP.get(extension, "unknown")
                
                file_info = {
                    "path": str(relative_path).replace("\\", "/"),
                    "language": language,
                    "size": file_path.stat().st_size,
                    "extension": extension,
                    "metadata": {}
                }
                
                # Parse content if supported and parser available
                if language == "python" and py_parser:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        file_info["metadata"] = py_parser.parse(content)
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
                
                results.append(file_info)
                    
        logger.info(f"Scanned {len(results)} files in {repo_path}")
        return results

    def get_file_content(self, repo_path: Path, file_relative_path: str) -> str:
        """
        Safely read file content.
        """
        full_path = repo_path / file_relative_path
        
        # Security check: ensure path is within repo
        try:
            full_path.resolve().relative_to(repo_path.resolve())
        except ValueError:
            raise ValueError(f"Invalid file path: {file_relative_path}")
            
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_relative_path}")
            
        try:
            # Try UTF-8 first
            return full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 for some legacy files, or just fail
            logger.warning(f"UTF-8 decode failed for {file_relative_path}, trying latin-1")
            return full_path.read_text(encoding="latin-1")
