
from src.interface import DataInterface
from src.marketsimulator import MarketSimulator, IdealFillSlippageModel, ZeroCostStructure

from example_strategies.reversion import RangeBound

API_KEY = "YOUR_API_KEY"
API_KEY = "vaKxLEdcRQssFpe6vHdFpj7VegVZPj8L"
STOCK = "LLY"
DATES = ["2025-07-14", "2025-07-15", "2025-07-16", "2025-07-17", "2025-07-18"]

if __name__ == "__main__":

    DI = DataInterface(API_KEY, STOCK, DATES)
    MS = MarketSimulator(slippage_model=IdealFillSlippageModel(), cost_structure=ZeroCostStructure())
    Strategy = RangeBound(mean=783.77, deviation=6.33, max_allowed_position=100)

    sample = DI.next_sample()

    while sample:

        order_qty, buy_side = Strategy.get_order(sample.NBBO, MS.positions.get(STOCK, 0))

        if order_qty != 0:
            MS.fill_order(STOCK, sample.NBBO, order_qty, sample.temporal, buy_side)
        
        sample = DI.next_sample()


    print(f"Final PnL for {STOCK}: {MS.get_stock_Pnl(STOCK)}")