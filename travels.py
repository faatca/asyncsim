import argparse
import datetime
import logging
import sys

from simloop import sched
from simloop.tracing import Trace

log = logging.getLogger(__name__)
trace = Trace()


def main():
    parser = argparse.ArgumentParser(description="Simulates our trip")
    parser.add_argument("-v", "--verbose", action="store_true", help="shows debug messages")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )

    try:
        sched.new_task(jm_camp())
        sched.new_task(aaron_camp())
        sched.run()
        print_activities()
    except Exception:
        log.exception("Unexpected error encountered")
        sys.exit(-1)
    else:
        log.info("Operation completed")


def print_activities():
    events = []
    for entry in trace.activities:
        events.append((entry.start_time, entry.id, "begin", entry.description))
        events.append((entry.end_time, entry.id, "end", entry.description))
    events.sort()

    level = 0
    for event in events:
        time, id, action, description = event
        if action == "begin":
            level += 1
        print(" " * level, time, action, description)
        if action == "end":
            level -= 1


class Location:
    def __init__(self, name):
        self.name = name


IN_TRANSIT = Location("In Transit")


class Person:
    def __init__(self, name, location):
        self.name = name
        self.location = location

    async def drive(self, vehicle, to, with_=None):
        if vehicle.location != self.location:
            message = f"{self.name}@{self.location} and {vehicle.name}@{vehicle.location} are in different locations"
            raise Exception(message)

        with trace.activity(f"{self.name} drives {vehicle.name} to {to.name}"):
            cargo = [] if with_ is None else list(with_)
            cargo.append(self)

            vehicle.pick_up(cargo)
            await vehicle.drive_to(to)
            vehicle.drop_off(cargo)

    async def load(self, item, into, period=None):
        with trace.activity(f"{self.name} loads {item.name} to {into.name}"):
            if period is not None:
                await sched.sleep(period)
            into.pick_up([item])

    async def unload(self, item, from_, period=None):
        with trace.activity(f"{self.name} unloads {item.name} from {from_.name}"):
            if period is not None:
                await sched.sleep(period)
            from_.drop_off([item])


class Thing:
    def __init__(self, name, location):
        self.name = name
        self.location = location


class Vehicle:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.payload = set()

    async def drive_to(self, location):
        # TODO: X Use real distances and times
        transit_time = datetime.timedelta(minutes=30)
        self.location = IN_TRANSIT
        await sched.sleep(transit_time)
        self.location = location

    def pick_up(self, items):
        for item in items:
            if item.location != self.location:
                raise Exception(
                    f"{item.name} needs to be at {self.location.name}, not {item.location.name}"
                )
            item.location = self
            self.payload.add(item)

    def drop_off(self, items):
        for item in items:
            self.payload.remove(item)
            assert item.location == self
            item.location = self.location


class Trailer:
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.payload = set()

    def pick_up(self, items):
        for item in items:
            self.payload.add(item)

    def drop_off(self, items):
        for i in items:
            self.payload.remove(i)


farm = Location(name="Sauer Farm")
home = Location(name="Home")
waterton = Location(name="Waterton")
mountain_view = Location(name="Mountain View")
hill_spring = Location(name="Hill Spring")
payne_lake = Location(name="Payne Lake")
sloan_cabin = Location(name="Sloan Cabin")
calgary = Location(name="Calgary")
edmonton = Location(name="Edmonton")
kimball = Location(name="Kimball")


aaron = Person(name="Aaron", location=home)
jm = Person(name="JM", location=home)
logan = Person(name="Logan", location=home)
bridget = Person(name="Bridget", location=home)
alyssa = Person(name="Alyssa", location=home)
benjamin = Person(name="Benjamin", location=calgary)
alyssa = Person(name="Alyssa", location=edmonton)

severus = Vehicle(name="Severus", location=home)
stephano = Vehicle(name="Stephano", location=home)

bucky = Trailer(name="Bucky", location=mountain_view)
ralph = Trailer(name="Ralph", location=home)

camping_stuff = Thing(name="Camping Stuff", location=mountain_view)
bucky.pick_up([camping_stuff])

minute = datetime.timedelta(minutes=1)
hour = datetime.timedelta(hours=1)


async def jm_camp():
    await sched.sleep_until("2022-07-14T09:00:00")
    with trace.activity("JM drive to Kimball"):
        await jm.drive(stephano, to=kimball, with_=[bridget])

    with trace.activity("Stay at Perretts with YW camp"):
        await sched.sleep_until("2022-07-15T09:00")

    with trace.activity("Drive into Waterton"):
        await jm.drive(stephano, to=waterton, with_=[bridget])

    with trace.activity("Wait for Bridget and car"):
        await sched.sleep(5 * hour)

    with trace.activity("Set up camp"):
        await jm.unload(bucky, from_=severus, period=20 * minute)
        await jm.unload(camping_stuff, from_=bucky, period=90 * minute)


async def aaron_camp():
    await sched.sleep_until("2022-07-14T09:00:00")
    with trace.activity("Pick up and load ralph"):
        await aaron.load(ralph, into=severus, period=15 * minute)
        # await aaron.load(camping_stuff, into=ralph, period=15 * minute)

    with trace.activity("Drive out to YM camp"):
        await aaron.drive(severus, to=kimball, with_=[logan])
        await aaron.unload(ralph, from_=severus, period=15 * minute)
        await aaron.drive(severus, to=mountain_view, with_=[logan])

        with trace.activity("Grab camp stuff from Bucky"):
            await sched.sleep(10 * minute)

        await aaron.drive(severus, to=sloan_cabin, with_=[logan])

    with trace.activity("Hang out at YM camp"):
        await sched.sleep_until("2022-07-15T09:00:00")

    with trace.activity("Go into Waterton for the hike"):
        with trace.activity("Go pick up Bucky"):
            await aaron.drive(severus, to=bucky.location, with_=[logan])
            await aaron.load(bucky, into=severus, period=15 * minute)

        await aaron.drive(severus, to=waterton, with_=[logan])

        with trace.activity("Hike"):
            await sched.sleep_until("2022-07-15T10:00:00")
            await sched.sleep(datetime.timedelta(hours=8))

        await aaron.drive(stephano, to=sloan_cabin, with_=[logan])

    with trace.activity("Finish YM camp"):
        await sched.sleep_until("2022-07-15T12:00:00")
        await aaron.drive(stephano, to=waterton, with_=[logan])

    with trace.activity("Stay in Waterton"):
        # Wait until Monday
        await sched.sleep_until("2022-07-24T10:00:00")

    with trace.activity("Pick up ralph"):
        await aaron.drive(severus, to=kimball)
        await aaron.load(ralph, into=severus, period=15 * minute)
        await aaron.drive(severus, to=waterton)
        await aaron.unload(ralph, from_=severus)


if __name__ == "__main__":
    main()
