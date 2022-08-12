import datetime
import logging

from simloop import sched, AsyncQueue

log = logging.getLogger(__name__)


def main():
    q = AsyncQueue()
    sched.new_task(producer(q, 9))
    sched.new_task(consumer(q))
    sched.run()


async def producer(q, count):
    for i in range(count):
        print("Producing", i, sched.time)
        await q.put(i)
        await sched.sleep(datetime.timedelta(hours=1, minutes=2))
    await q.put(None)


async def consumer(q):
    while True:
        item = await q.get()
        if item is None:
            break
        print("Consuming", item, sched.time)
    print("Consumer done")


if __name__ == "__main__":
    main()
