"""
Gradio conversational front-end for the Degree Requirement Navigator.

Uses the SAME Supabase project and the SAME backend API as the React app —
a user logs in here with the same email/password they'd use on the website,
and the chat is personalized (it knows their completed courses) because the
backend verifies the same Supabase-issued JWT either way.

Only the anon key is used here for sign-in; it is subject to Supabase's
Row Level Security policies just like in the browser, so this process never
holds a credential capable of reading another student's data.
"""

import os

import gradio as gr
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def do_login(email: str, password: str):
    if not email or not password:
        return None, gr.update(value="Enter your email and password."), gr.update(visible=True), gr.update(visible=False)
    try:
        # Calls Supabase's Auth REST API directly (same endpoint the
        # supabase-js client in the React app uses under the hood) — this
        # keeps the Gradio app's dependencies light and avoids pulling in
        # the full supabase-py SDK (whose realtime extra has a websockets
        # version conflict with gradio) just for a password sign-in.
        resp = httpx.post(
            f"{SUPABASE_URL}/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("error_description", exc.response.text)
        return None, gr.update(value=f"Login failed: {detail}"), gr.update(visible=True), gr.update(visible=False)
    except Exception as exc:  # noqa: BLE001 — surface auth errors to the user
        return None, gr.update(value=f"Login failed: {exc}"), gr.update(visible=True), gr.update(visible=False)

    return token, gr.update(value=""), gr.update(visible=False), gr.update(visible=True)


def do_logout():
    return None, gr.update(visible=True), gr.update(visible=False), []


def chat_fn(message: str, history: list, token: str | None):
    if not token:
        return history + [{"role": "assistant", "content": "You're not logged in — please log in first."}]
    try:
        resp = httpx.post(
            f"{API_BASE_URL}/agent/chat",
            json={"message": message},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        resp.raise_for_status()
        reply = resp.json()["reply"]
    except httpx.HTTPStatusError as exc:
        reply = f"Backend error ({exc.response.status_code}): {exc.response.text}"
    except Exception as exc:  # noqa: BLE001
        reply = f"Something went wrong: {exc}"
    return history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]


with gr.Blocks(title="Degree Requirement Navigator") as demo:
    token_state = gr.State(value=None)

    with gr.Column(visible=True) as login_col:
        gr.Markdown("## Degree Requirement Navigator — log in")
        email_box = gr.Textbox(label="Email")
        password_box = gr.Textbox(label="Password", type="password")
        login_error = gr.Markdown()
        login_btn = gr.Button("Log in", variant="primary")

    with gr.Column(visible=False) as chat_col:
        gr.Markdown("## Ask the navigator")
        chatbot = gr.Chatbot(type="messages", height=450)
        msg_box = gr.Textbox(label="Your question", placeholder="What do I still need for my CS Electives (400+)?")
        logout_btn = gr.Button("Log out")

    login_btn.click(
        do_login,
        inputs=[email_box, password_box],
        outputs=[token_state, login_error, login_col, chat_col],
    )

    msg_box.submit(
        chat_fn,
        inputs=[msg_box, chatbot, token_state],
        outputs=[chatbot],
    ).then(lambda: "", outputs=[msg_box])

    logout_btn.click(do_logout, outputs=[token_state, login_col, chat_col, chatbot])


if __name__ == "__main__":
    demo.launch()
