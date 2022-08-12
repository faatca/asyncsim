import argparse
import datetime
import logging
import sys

from simloop import sched

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Simulates finances")
    parser.add_argument("-v", "--verbose", action="store_true", help="shows debug messages")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )

    try:
        sched.new_task(handle_banks())
        sched.new_task(work())
        log.debug("Running")
        sched.run_until("2050-01-01")

        for bank in banks:
            for account in bank.accounts:
                print(f"## Account {account.name}")
                for t, description, amount, balance in account.transactions:
                    print(f"{t} {description} {amount:.02f} {balance:.02f}")
                print()

    except Exception:
        log.exception("Unexpected error encountered")
        sys.exit(-1)
    else:
        log.info("Operation completed")


async def work():
    await sched.sleep_until("2022-06-01")
    atb.open_account("checking", balance=15000)
    atb.open_account("rrsp", balance=30000, rate=0.07)
    atb.open_account("savings", balance=3000, rate=0.01)


async def handle_banks():
    while True:
        tomorrow = sched.time.date() + datetime.timedelta(days=1)
        await sched.sleep_until(tomorrow)
        log.debug(tomorrow)
        for bank in banks:
            for account in bank.accounts:
                account.handle_new_day()


class Bank:
    def __init__(self, name):
        self.name = name
        self.accounts = []

    def open_account(self, name, balance=0, rate=0):
        account = Account(name, rate=rate, balance=balance)
        self.accounts.append(account)
        log.debug(f"Opening account {name} with balance {balance} and rate {rate}")


class Account:
    def __init__(self, name, *, balance=0, rate=0):
        self.name = name
        self.balance = 0
        self.month_rate = rate / 12
        self.transactions = []

        if balance:
            self.transfer("Opening balance", balance)

        self._daily_balance_total = 0
        self._daily_balance_count = 0

    def transfer(self, description, amount):
        self.balance += amount
        transaction = (sched.time, description, amount, self.balance)
        self.transactions.append(transaction)

    def handle_new_day(self):
        if sched.time.day == 1:
            average_balance = (
                (self._daily_balance_total / self._daily_balance_count)
                if self._daily_balance_count
                else 0
            )
            interest = round(average_balance * self.month_rate, 2)
            if interest:
                log.debug("Recording interest: %s", interest)
                self.transfer("Interest", interest)
            self._daily_balance_total = 0
            self._daily_balance_count = 0
        log.debug("yo")
        self._daily_balance_total += self.balance
        self._daily_balance_count += 1


atb = Bank("ATB")
banks = [atb]


if __name__ == "__main__":
    main()
