from flask import Flask

from scheduler import Scheduler

app = Flask(__name__)


@app.route("/", methods=["GET"])
def hello_world():
    scheduler = Scheduler()
    data = scheduler.get_schedule()
    return data
