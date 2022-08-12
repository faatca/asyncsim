from collections import deque
import heapq
import datetime


class Awaitable:
    def __await__(self):
        yield


def switch():
    return Awaitable()


ZERO_DELTA = datetime.timedelta()


class Scheduler:
    def __init__(self):
        self.ready = deque()
        self.sleeping = []
        self.current = None
        self.sequence = 0
        self.time = datetime.datetime.fromisoformat("2000-01-01")

    async def sleep(self, delay):
        deadline = self.time + delay
        self.sequence += 1
        heapq.heappush(self.sleeping, (deadline, self.sequence, self.current))
        self.current = None
        await switch()

    async def sleep_until(self, deadline):
        deadline = parse_deadline(deadline)

        self.sequence += 1
        heapq.heappush(self.sleeping, (deadline, self.sequence, self.current))
        self.current = None
        await switch()

    def new_task(self, coro):
        self.ready.append(coro)

    def run(self):
        while self.ready or self.sleeping:
            if not self.ready:
                deadline, _, coro = heapq.heappop(self.sleeping)
                delta = deadline - self.time
                if delta > ZERO_DELTA:
                    self.time = deadline
                self.ready.append(coro)

            self.current = self.ready.popleft()

            try:
                self.current.send(None)
                if self.current:
                    self.ready.append(self.current)
            except StopIteration:
                pass

    def run_until(self, deadline):
        async def stopper():
            await self.sleep_until(deadline)
            raise EndOfSimulationException

        deadline = parse_deadline(deadline)
        self.new_task(stopper())
        try:
            self.run()
        except EndOfSimulationException:
            pass


def parse_deadline(deadline):
    if isinstance(deadline, str):
        return datetime.datetime.fromisoformat(deadline)
    if isinstance(deadline, datetime.date):
        return datetime.datetime.combine(deadline, datetime.time())
    return deadline


class EndOfSimulationException(Exception):
    pass


sched = Scheduler()


class AsyncQueue:
    def __init__(self):
        self.items = deque()
        self.waiting = deque()

    async def put(self, item):
        self.items.append(item)
        if self.waiting:
            sched.ready.append(self.waiting.popleft())

    async def get(self):
        if not self.items:
            self.waiting.append(sched.current)
            sched.current = None
            await switch()
        return self.items.popleft()


class Event:
    def __init__(self):
        self.waiting = deque()
        self.value = False

    def set(self):
        self.value = True
        if self.waiting:
            while self.waiting:
                sched.ready.append(self.waiting.popleft())

    def is_set(self):
        return self.value

    async def wait(self):
        if not self.value:
            self.waiting.append(sched.current)
            sched.current = None
            await switch()
