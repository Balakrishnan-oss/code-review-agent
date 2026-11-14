import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

MODEL = "gemini-3.5-flash"  # change to gemini-2.5-flash if this is what worked in hello.py


# 1. Describe the exact shape of the answer we want
class Issue(BaseModel):
    line: int
    severity: str  # high, medium or low
    problem: str
    fix: str


# 2. Read the file name you give in the terminal
file_path = sys.argv[1]
with open(file_path) as f:
    code = f.read()

# 3. Tell the AI its job
prompt = f"""You are a senior Python code reviewer.
Find real bugs, security problems and bad practices in the code below.
Give the line number, severity (high, medium or low), the problem, and a fix.
If there are no issues, return an empty list.

CODE:
{code}
"""

# 4. Send it, and force the answer into our shape
client = genai.Client()
response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=list[Issue],
    ),
)

# 5. The answer is already clean Python objects
for issue in response.parsed:
    print(f"Line {issue.line} [{issue.severity}]")
    print(f"  Problem: {issue.problem}")
    print(f"  Fix:     {issue.fix}")
    print()
