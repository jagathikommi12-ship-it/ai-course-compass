import json

import anthropic

from app.agent.tools import TOOL_SCHEMAS, dispatch_tool
from app.config import get_settings

SYSTEM_PROMPT = """\
You are the Degree Requirement Navigator, an assistant that helps students \
figure out what they still need for their major/minor, whether a specific \
elective counts toward a requirement, and what they're now eligible to take.

Rules:
- Never guess or calculate requirement fulfillment yourself. Always call the \
provided tools to check prerequisites, requirement status, and eligibility — \
they are backed by the real database, and your own arithmetic on course \
lists is not trustworthy enough for something a student will act on.
- Before confirming that a cross-listed or unusual-looking course counts \
toward a requirement, call check_course_ambiguity. If it returns a caveat, \
surface it to the student plainly (e.g. "this may not count if you took the \
other cross-listed section — double check with your advisor") rather than \
giving a flat yes.
- If a course code the student mentions doesn't resolve directly, use \
search_courses to find the right one before giving up.
- Be concise and concrete: name exact course codes and counts ("you still \
need 2 more of: CS 320, CS 350, CS 445"), not vague summaries.
"""

MAX_TOOL_ITERATIONS = 8


class DegreeNavigatorAgent:
    def __init__(self, user_id: str):
        self.user_id = user_id
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def chat(self, message: str, history: list[dict] | None = None) -> str:
        messages = list(history or [])
        messages.append({"role": "user", "content": message})

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                return "".join(
                    block.text for block in response.content if block.type == "text"
                )

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                try:
                    result = dispatch_tool(block.name, block.input, self.user_id)
                except Exception as exc:  # noqa: BLE001 — surface to the model, not a 500
                    result = {"error": str(exc)}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return "Sorry, I couldn't finish reasoning about that in time — please try rephrasing or ask a more specific question."
