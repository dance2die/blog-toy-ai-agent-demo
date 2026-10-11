# src/main.py
import asyncio
import time
import httpx
import inspect
import json
from tools import TOOLS, ALLOWED_TOOLS, MAX_MODEL_TURNS


# From LM Stuio Server: OpenAI-compatible API endpoint
URL = "http://127.0.0.1:1234/v1/chat/completions"
# LM Studio loaded this model
MODEL = "google/gemma-4-12b"


async def handle_user_messages(client, messages):
    # how many times (MAX_MODEL_TURNS) do we want to let LLM call tools?
    for turn in range(MAX_MODEL_TURNS):
        started = time.perf_counter()
        response = await ask_model(client, messages)
        tool_calls = response.get("tool_calls") or []
        print(
            f"turn={turn + 1} "
            f"model_seconds={time.perf_counter() - started:.2f} "
            f"tool_calls={len(tool_calls)}"
        )

        # LLM did not request tool call
        if not tool_calls:
            answer = response.get("content") or ""
            messages.append({"role": "assistant", "content": answer})
            return answer

        # Do not begin more tool work on the final allowed model turn.
        if turn == MAX_MODEL_TURNS - 1:
            answer = "Stopped: reached the model-turn limit"
            messages.append({"role": "assistant", "content": answer})
            return answer

        # Save the tool call HISTORY to short-term lived context
        tool_request = {
            "role": "assistant",
            "tool_calls": tool_calls,
        }
        if response.get("content") is not None:
            tool_request["content"] = response["content"]
        messages.append(tool_request)

        for call in tool_calls:
            try:
                result = run_tool(call)
            except (ValueError, TypeError, KeyError) as error:
                result = f"Tool error: {error}"

            # Save the tool call RESULT to short-term lived context
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": str(result),
            })
    return "Stopped: reached the model-turn limit."


def run_tool(tool_call):
    name = tool_call["function"]["name"]
    # Verify if the model can use the tool
    function = ALLOWED_TOOLS.get(name)
    if function is None:
        raise ValueError(f"Unknown tool: {name}")

    args = json.loads(tool_call["function"]["arguments"])

    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be a JSON object")

    # Verify if correct argument type is passed by model
    inspect.signature(function).bind(**args)
    # To see if tool is called
    print("Requested tool:", function.__name__, args)
    # Call the tool
    return function(**args)


async def ask_model(client, messages):
    response = await client.post(
        URL,
        json={
            "model": MODEL,
            "messages": messages,
            # Tools that the model can use
            "tools": TOOLS,
            "stream": False,
        },
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]


async def main():
    # Extracted "messages" from "payload".
    messages = [{
        "role": "system", 
        "content": """Be concise.
        Use add for addition.
        When asked to remember something, call save_note before confirming.
        When asked to recall a saved note, call search_notes before answering.
        Use query="*" to list all notes.
        Never claim a note was saved or found unless the tool result confirms it.
        """
    }]

    async with httpx.AsyncClient(timeout=120) as client:
        # 1. REPL loop
        while True:
            user_prompt = input("Enter prompt (or quit)> ")
            if user_prompt.casefold() in {"quit", "exit", "q", "e"}:
                break

            # What we are passing to LLM
            messages.append({"role": "user", "content": user_prompt})
            # Abstracted LLM and tool calls
            answer = await handle_user_messages(client, messages)
            print(f"Agent: {answer}")



if __name__ == "__main__":
    asyncio.run(main())