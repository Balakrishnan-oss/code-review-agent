import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-3.5-flash"  # use the same name that worked in review.py
MAX_STEPS = 8               # safety limit so the agent can't loop forever

# The folder the agent is allowed to look at
ROOT = Path(sys.argv[1]).resolve()


def _safe(path: str) -> Path:
    """Safety guard: the agent may never read files outside the project folder."""
    full = (ROOT / path).resolve()
    if not full.is_relative_to(ROOT):
        raise ValueError("Path is outside the project folder")
    return full


# ---------- TOOLS (plain Python functions the AI can ask us to run) ----------

def list_files() -> str:
    """List all Python files in the project."""
    files = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py"))
    return "\n".join(files) or "No Python files found."


def read_file(path: str) -> str:
    """Read a file in the project and return its text with line numbers.
    path is relative to the project folder, for example 'utils.py'."""
    try:
        text = _safe(path).read_text()
    except Exception as e:
        return f"ERROR: {e}"
    return "\n".join(f"{i}: {line}" for i, line in enumerate(text.splitlines(), 1))


def search_code(keyword: str) -> str:
    """Search every Python file for a keyword, for example a function name.
    Returns file, line number and the matching line."""
    hits = []
    for p in ROOT.rglob("*.py"):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if keyword in line:
                hits.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    return "\n".join(hits[:30]) or "No matches."


def run_linter(path: str) -> str:
    """Run the Ruff linter on a file and return the problems it finds.
    path is relative to the project folder, for example 'utils.py'."""
    try:
        target = _safe(path)
    except Exception as e:
        return f"ERROR: {e}"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(target), "--output-format", "concise"],
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr).strip() or "No linter problems found."


TOOLS = {f.__name__: f for f in [list_files, read_file, search_code, run_linter]}

# ---------- THE AGENT ----------

SYSTEM = """You are a careful senior Python code reviewer.
Use your tools to investigate before you answer:
- list the files, then read each one
- run the linter on each file
- when a function looks suspicious, search for where it is called, to check how it is really used
Only report real problems. For each one give: file, line number, severity (high/medium/low),
what is wrong, and how to fix it. Finish with a short summary."""

client = genai.Client()

config = types.GenerateContentConfig(
    system_instruction=SYSTEM,
    tools=list(TOOLS.values()),
    # We run the loop ourselves, so turn off the SDK's automatic loop
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

# The conversation so far. It grows with every step.
contents = [
    types.Content(
        role="user",
        parts=[types.Part(text="Please review this Python project.")],
    )
]

for step in range(1, MAX_STEPS + 1):
    # 1. Ask the AI what to do next
    response = client.models.generate_content(
        model=MODEL, contents=contents, config=config
    )
    contents.append(response.candidates[0].content)

    # 2. If it asked for no tools, it is done
    calls = response.function_calls
    if not calls:
        break

    # 3. Otherwise run each tool it asked for and send the results back
    result_parts = []
    for call in calls:
        print(f"[step {step}] tool: {call.name}({dict(call.args)})")
        tool = TOOLS.get(call.name)
        result = tool(**call.args) if tool else f"ERROR: unknown tool {call.name}"
        result_parts.append(
            types.Part.from_function_response(
                name=call.name, response={"result": result}
            )
        )
    contents.append(types.Content(role="user", parts=result_parts))
else:
    print("Stopped: reached the step limit.")

print("\n===== REVIEW =====\n")
print(response.text)
