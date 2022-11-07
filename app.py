from flask import Flask
from scheduler import Scheduler

app = Flask(__name__)


@app.route("/")
def hello_world():
    scheduler = Scheduler()
    return scheduler.get_schedule()
