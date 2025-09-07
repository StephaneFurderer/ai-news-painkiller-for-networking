import os, json, modal
from fastapi import Request, Response, BackgroundTasks
from helpers.functions.send_profile_to_db import send_profile_to_db
from helpers.functions.discord_request import extract_verified_body
from helpers.commands.news import run_news_updates
from helpers.commands.setup import (             
    handle_setup_command,                
    handle_setup_button_interaction,    
    handle_modal_submission,             
)

APP_NAME = "modal-webhook-echo"
SECRET_NAME = "safron-bot"

def create_image():
    return modal.Image.debian_slim().pip_install(
        "fastapi>=0.110",
        "requests",
        "pydantic",
        "PyNaCl",
        "aiohttp",
        "llama-index-core",
        "llama-index-llms-gemini",
        "google-generativeai",
        "google-genai",
        "llama-index-llms-openai",
        "openai",
        "pymongo[srv]>=4.6"
    ).add_local_python_source("helpers")

app = modal.App(APP_NAME, secrets=[modal.Secret.from_name(SECRET_NAME)])
image = create_image()

@app.function(image=image, cpu=0.125, scaledown_window=300, min_containers=1, timeout=900, secrets=[modal.Secret.from_name(SECRET_NAME)])
@modal.fastapi_endpoint(method="POST")
async def discord_interactions(request: Request, background_tasks: BackgroundTasks):
    body = await extract_verified_body(request)
    if body is None:
        return Response(status_code=401)

    data = json.loads(body.decode("utf-8"))
    t = data.get("type")

    if t == 1:
        return {"type": 1}

    if t == 2:
        cmd = data.get("data", {}).get("name")
        user = (data.get("member") or {}).get("user") or {}
        user_id, user_name, global_name = user.get("id"), user.get("username"), user.get("global_name")

        if cmd == "setup":
            return await handle_setup_command(data, user_id, user_name, global_name)
        
        if cmd == "news":
            application_id = data.get("application_id")
            token = data.get("token")
            channel_id = data.get("channel_id")
            options = data.get("data", {}).get("options", [])

            time_period_override = None
            for option in options:
                if option.get("name") == "time_period":
                    time_period_override = option.get("value")
                    break
            
            if application_id and token and user_id:
                background_tasks.add_task(run_news_updates, application_id, token, user_id, time_period_override, channel_id)
            return {"type": 5, "data": {"flags": 64}}

        return {"type": 4, "data": {"content": "Unknown command", "flags": 64}}

    if t == 3:
        resp = await handle_setup_button_interaction(data)
        return resp or {"type": 6}

    if t == 5:
        try:
            result = await handle_modal_submission(data)
            if not result:
                return {"type": 6}
            response_payload, profile_data = result
            application_id = data.get("application_id")
            token = data.get("token")
            background_tasks.add_task(send_profile_to_db, profile_data, application_id, token)
            return response_payload
        except Exception as e:
            print(f"Error in modal submission: {e}")
            return {"type": 4, "data": {"content": "An error occurred processing your submission.", "flags": 64}}

    return Response(status_code=200)

