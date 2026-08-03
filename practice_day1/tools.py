"""
Tools for the Coding Agent — YOUR FILE
========================================

Implement the 3 tools below. The agent (LLM) will decide
WHEN and HOW to call them based on the docstring.

Remember: the LLM never sees your code — only the function name,
docstring, and parameter types.
"""

import subprocess

from langchain_core.tools import tool

from config import REPO_PATH


@tool
def get_file_content(path: str) -> str:
    """Read a file from the repository. Returns the full file content as a string.

    Args:
        path: Relative path to the file within the repository (e.g., "app.py", "models.py")
    """
    file_path = REPO_PATH / path
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except OSError as e:
        return f"Error reading {path}: {e}"



@tool
def search_codebase(query: str) -> str:
    """Search across the codebase for functions, classes, or patterns matching the query.
    Returns relevant file paths and matched lines.

    Args:
        query: Search term — a function name, class name, keyword, or pattern
    """
    matches = []
    for file_path in REPO_PATH.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        relative_path = file_path.relative_to(REPO_PATH)
        for lineno, line in enumerate(lines, start=1):
            if query in line:
                matches.append(f"{relative_path}:{lineno}:{line.strip()}")

    if not matches:
        return f"No matches found for '{query}'."
    return "\n".join(matches)


@tool
def get_git_diff(commit_a: str, commit_b: str) -> str:
    """Return the diff between two commits or branches.
    Useful for understanding what changed and why.

    Args:
        commit_a: First commit hash or branch name (e.g., "HEAD~3")
        commit_b: Second commit hash or branch name (e.g., "HEAD")
    """
    result = subprocess.run(
        ["git", "diff", commit_a, commit_b],
        cwd=REPO_PATH,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return f"Error running git diff: {result.stderr}"
    return result.stdout or "No differences found."


# All tools in a list — used by the agent
all_tools = [get_file_content, search_codebase, get_git_diff]
