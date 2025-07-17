### example1.py ###
#
# Shows very basic usage of the DataInterface class
# Raw use without any additional processing or wrappers
#

from src.interface import DataInterface


API_KEY = "YOUR_API_KEY"
STOCK = "VOYG"
DATES = ["2025-07-15", "2025-07-16"]


if __name__ == "__main__":

    DI = DataInterface(API_KEY, STOCK, DATES)

    sample = DI.next_sample()
    while sample:
        print(f"Bid: {sample.NBBO.get('bid')}, Ask: {sample.NBBO.get('ask')}, Last Trade Price: {sample.last_trade.get('price')}")
        sample = DI.next_sample()