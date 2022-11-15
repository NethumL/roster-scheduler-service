import os
import threading

import requests
from flask import Flask, request

from scheduler import Scheduler

app = Flask(__name__)


def prepare_and_send_schedule(data):
    scheduler = Scheduler()
    info = scheduler.schedule(data)
    print(info)
    result = {"schedule": scheduler.solution, "data": data["data"]}
    response = requests.post(
        os.getenv("RESPONSE_ENDPOINT"),
        json=result,
        headers={"X-secret": os.getenv("SECRET")},
    )
    print(response.status_code, response.content)


@app.route("/", methods=["POST"])
def get_schedule():
    if os.getenv("SECRET") != request.headers.get("X-secret", ""):
        return "", 401

    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        data = request.json
    else:
        return "Content-Type not supported!"

    t = threading.Thread(target=prepare_and_send_schedule, args=(data,))
    t.start()

    return {"success": True}
