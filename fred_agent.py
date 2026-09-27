"""The FRED agent from session 4, with an API bolted on.

It is the same agent: the FRED MCP server as its only source of data, plus a
run_python tool. The only new thing is that you can now reach it without
typing into a UI.

    export ANTHROPIC_API_KEY=sk-ant-...
    python -m uvicorn fred_agent:app --port 8001

Three ways in, all hitting the same agent:

    browser   http://localhost:8001/?unemployment and inflation over ten years

    curl      curl -s -X POST http://localhost:8001/ask \
                -H "Content-Type: application/json" \
                -d '{"question": "what is unemployment now?"}'

    python    requests.post("http://localhost:8001/ask",
                            json={"question": "..."}).json()["answer"]

Every request is its own conversation. Nothing is remembered between calls,
which is what makes this usable as somebody else's tool: the caller gets the
answer and none of the material behind it.

The terminal is the interesting view. Every FRED call and every line of
Python the agent writes is printed there as it happens.
"""

import io
import os
import sys
import traceback
from contextlib import contextmanager, redirect_stdout

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

MODEL = "claude-opus-5"
FRED_URL = "https://fred.kerryback.com/mcp"

SYSTEM = """You answer questions about US economic data.

FRED is your only source of numbers. Never state a figure you did not fetch
from it, and never fill a gap from memory. Say which series ID a number came
from.

Use run_python for arithmetic, percentage changes, and anything else you would
otherwise do in your head.

Answer in plain prose. No markdown, no asterisks, no bullet points. Keep it
short enough to read aloud."""


# ---------------------------------------------------------------- run_python

class NoNetwork(Exception):
    """Raised when code inside run_python tries to open a connection."""


@contextmanager
def _no_network():
    """Make run_python compute-only for the duration of one exec.

    Without this the agent skips the FRED tools entirely and does
    pd.read_csv("https://fred.stlouisfed.org/...") instead, which is a
    different program from the one the slides describe. run_python runs
    in this process; the MCP connection lives in the CLI subprocess, so
    blocking sockets here leaves FRED reachable.

    One demo at a time: this patches the module globally while exec runs,
    so concurrent requests would be affected too.
    """
    import socket

    def blocked(*args, **kwargs):
        raise NoNetwork(
            "run_python has no network access. Use the fred_ tools to get data, "
            "then compute with it here."
        )

    saved = socket.socket, socket.create_connection
    socket.socket, socket.create_connection = blocked, blocked
    try:
        yield
    finally:
        socket.socket, socket.create_connection = saved


@tool(
    "run_python",
    "Compute with Python and return whatever it prints. pandas is available as "
    "pd. No network access: get data with the fred_ tools first, paste it in, "
    "and do the arithmetic here. Print your results — a value that is not "
    "printed is not returned.",
    {"code": str},
)
async def run_python(args):
    code = args["code"]
    print(f"\n  run_python\n{_indent(code)}")
    buffer = io.StringIO()
    namespace = {}
    try:
        import pandas as pd

        namespace["pd"] = pd
    except ImportError:
        pass
    try:
        with redirect_stdout(buffer), _no_network():
            exec(code, namespace)
        out = buffer.getvalue().strip() or "(printed nothing)"
    except Exception:
        out = buffer.getvalue() + "\n" + traceback.format_exc(limit=3)
    print(f"  -> {_indent(out, 5).lstrip()}")
    return {"content": [{"type": "text", "text": out}]}


python_server = create_sdk_mcp_server("local", tools=[run_python])


# ------------------------------------------------------------------ the agent

FRED_TOOLS = [
    "mcp__fred__fred_list_catalog",
    "mcp__fred__fred_search_series",
    "mcp__fred__fred_series_info",
    "mcp__fred__fred_get_observations",
    "mcp__fred__fred_get_vintage",
]

OPTIONS = ClaudeAgentOptions(
    model=MODEL,
    system_prompt=SYSTEM,
    mcp_servers={
        "fred": {"type": "http", "url": FRED_URL},
        "local": python_server,
    },
    # No Bash, no Read, no WebSearch, no WebFetch — the FRED tools and Python,
    # nothing else. A short tool list is not by itself a closed door: run_python
    # execs arbitrary code, and left alone it reached the web through pandas and
    # skipped the FRED server entirely. _no_network() is what actually stops it.
    tools=[],
    allowed_tools=FRED_TOOLS + ["mcp__local__run_python"],
    permission_mode="bypassPermissions",
    max_turns=30,
)


async def ask(question: str) -> str:
    """Run the agent once and return its answer as plain text."""
    print(f"\n{'=' * 70}\n>>> {question}\n{'=' * 70}")
    answer_parts: list[str] = []
    async for message in query(prompt=question, options=OPTIONS):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    if block.name != "mcp__local__run_python":
                        print(f"\n  {block.name.replace('mcp__fred__', 'fred: ')}")
                        print(f"{_indent(_short(block.input))}")
                elif isinstance(block, TextBlock):
                    answer_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            result = getattr(message, "result", None)
            if result:
                answer_parts = [result]
            cost = getattr(message, "total_cost_usd", None)
            turns = getattr(message, "num_turns", None)
            print(f"\n  [{turns} turns"
                  + (f", ${cost:.4f}" if isinstance(cost, float) else "")
                  + "]")
    answer = "\n".join(p.strip() for p in answer_parts if p and p.strip())
    print(f"\n{answer}\n")
    return answer or "(the agent returned nothing)"


def _indent(text: str, spaces: int = 6) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in str(text).splitlines())


def _short(value, limit: int = 300) -> str:
    text = str(value)
    return text if len(text) <= limit else text[:limit] + " ..."


# ------------------------------------------------------------------ the API

app = FastAPI(title="FRED agent")


class Question(BaseModel):
    question: str


async def _answer(question: str) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "No ANTHROPIC_API_KEY set. Export it and restart the server."
    try:
        return await ask(question)
    except Exception as e:
        traceback.print_exc()
        return f"{type(e).__name__}: {e}"


USAGE = """FRED agent.

Ask it something by putting the question in the URL:

    http://localhost:8001/?unemployment and inflation over the last ten years

Or POST to /ask with {"question": "..."} and get {"answer": "..."} back.
"""


@app.post("/ask")
async def ask_endpoint(body: Question):
    """The endpoint another agent calls. JSON in, JSON out."""
    return {"answer": await _answer(body.question)}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return PlainTextResponse("", status_code=204)


@app.get("/", response_class=PlainTextResponse)
async def browser(request: Request):
    """The same agent, reachable from the browser's address bar."""
    from urllib.parse import unquote_plus

    question = unquote_plus(request.url.query)
    if not question:
        return USAGE
    return await _answer(question)


if __name__ == "__main__":
    import asyncio

    question = " ".join(sys.argv[1:]) or "What is the unemployment rate now?"
    asyncio.run(ask(question))
