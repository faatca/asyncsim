from collections import namedtuple
import logging
from simloop import sched

log = logging.getLogger(__name__)


class Trace:
    def __init__(self):
        self.activities = []
        self.sequence = 0

    def activity(self, description):
        self.sequence += 1
        return Activity(self, description, self.sequence)


class Activity:
    def __init__(self, trace, description, activity_id):
        self.trace = trace
        self.activity_id = activity_id
        self.description = description
        self.start_time = sched.time

    def start(self):
        self.start_time = sched.time
        log.debug("Started activity at %s: %s", self.start_time, self.description)

    def finish(self):
        self.end_time = sched.time
        self.trace.activities.append(
            Entry(self.activity_id, self.start_time, self.end_time, self.description)
        )
        log.debug("Finished activity at %s: %s", self.end_time, self.description)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()
        return None


Entry = namedtuple("Entry", "id start_time end_time description")
