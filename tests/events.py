import datetime
from simloop import sched, Event

arrival = Event()


def main():
    sched.new_task(guest())
    sched.new_task(recipient())
    sched.run()


async def guest():
    print(sched.time, "Ok, I'm hiding")
    await arrival.wait()
    print(sched.time, "Boo! I'm here")
    print(sched.time, "Trying to hide again")
    await arrival.wait()
    print(sched.time, "Done")


async def recipient():
    print(sched.time, "Waiting a long time")
    await sched.sleep(datetime.timedelta(hours=4))
    print(sched.time, "Ok I'm here")
    arrival.set()
    print(sched.time, "I'm done")


if __name__ == "__main__":
    main()
