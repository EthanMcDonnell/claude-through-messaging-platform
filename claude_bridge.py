"""
Invokes the claude CLI with a prompt in a specific project directory.
Tool permissions are configured directly in config.yaml per project.
"""

import subprocess
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_TOOLS = ["Read", "Glob", "Grep", "LS"]


def ask_claude(prompt: str, project_path: str, allowed_tools: list[str], timeout: int = 120) -> str:
    """
    Run claude -p with the given prompt in the project directory.
    Returns the response text, or an error message if it fails.
    """
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return "Error: claude CLI not found in PATH."

    project_dir = Path(project_path).resolve()
    if not project_dir.is_dir():
        return f"Error: project directory not found: {project_path}"

    tools = allowed_tools or DEFAULT_ALLOWED_TOOLS
    tools_arg = ",".join(tools)

    cmd = [
        claude_bin,
        "-p", prompt,
        "--output-format", "text",
        "--allowedTools", tools_arg,
    ]

    logger.info("Invoking claude in %s (tools: %s)", project_dir, tools_arg)
    logger.debug("Prompt: %s", prompt[:200])

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            err = result.stderr.strip() or "Unknown error"
            logger.error("Claude exited with code %d: %s", result.returncode, err)
            return f"Claude error (code {result.returncode}): {err[:500]}"

        output = result.stdout.strip()
        if not output:
            return "Claude returned an empty response."
        return output

    except subprocess.TimeoutExpired:
        logger.error("Claude timed out after %ds", timeout)
        return f"Request timed out after {timeout} seconds."
    except Exception as e:
        logger.error("Unexpected error calling claude: %s", e)
        return f"Unexpected error: {e}"
