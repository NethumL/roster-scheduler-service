import os

from flask import Flask, request

from scheduler import Scheduler

app = Flask(__name__)


@app.route("/", methods=["POST"])
def get_schedule():
    if os.getenv("SECRET") != request.headers.get("X-secret", ""):
        return "", 401

    content_type = request.headers.get("Content-Type")
    if content_type == "application/json":
        data = request.json
    else:
        return "Content-Type not supported!"

    scheduler = Scheduler()
    info = scheduler.schedule(data)
    print(info)
    return scheduler.solution
