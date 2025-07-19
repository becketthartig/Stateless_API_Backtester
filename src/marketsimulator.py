class SlippageModel:
    
    """
    Base class for slippage models
    """

    def calculate_slippage(self, NBBO, order_qty, buy_side=True):
        raise NotImplementedError("Subclasses should implement this method.")

class IdealFillSlippageModel(SlippageModel):

    """
    No slippage always fills at NBBO bid/ask
    """

    def calculate_slippage(self, NBBO, order_qty, buy_side=True):
        if buy_side:
            return NBBO.get("ask"), order_qty
        else:
            return NBBO.get("bid"), order_qty

class BasicFractionalSlippageModel(SlippageModel):

    """
    Fills up to available size at NBBO, 
    remainder at worse price by slippage rate
    """

    def __init__(self, slippage_rate=0.001):
        self.slippage_rate = slippage_rate

    def calculate_slippage(self, NBBO, order_qty, buy_side=True):
        if buy_side:
            ask = NBBO.get("ask")
            ask_size = NBBO.get("ask_size", 0)
            if order_qty <= ask_size:
                return ask, order_qty
            else:
                optimal_fill = ask_size
                suboptimal_fill = order_qty - ask_size
                suboptimal_price = ask * (1 + self.slippage_rate)
                avg_price = (ask * optimal_fill + suboptimal_price * suboptimal_fill) / order_qty
                return avg_price, order_qty
        else:
            bid = NBBO.get("bid")
            bid_size = NBBO.get("bid_size", 0)
            if order_qty <= bid_size:
                return bid, order_qty
            else:
                optimal_fill = bid_size
                suboptimal_fill = order_qty - bid_size
                suboptimal_price = bid * (1 - self.slippage_rate)
                avg_price = (bid * optimal_fill + suboptimal_price * suboptimal_fill) / order_qty
                return avg_price, order_qty


class CostStructure:

    """
    Base class for cost structures
    """

    def calculate_cost(self, shares, avg_price):
        raise NotImplementedError("Subclasses should implement this method.")

class ZeroCostStructure(CostStructure):

    """
    No cost structure, always returns 0.0
    """

    def calculate_cost(self, shares, avg_price):
        return 0.0
    
class IBKRProFIXEDCostStructure(CostStructure):

    """
    IBKR Pro FIXED cost structure
    Charges 0.005 per share with a minimum of 1.00 and maximum of 1% of order value
    """

    def calculate_cost(self, shares, avg_price):

        PER_SHARE_FEE = 0.005
        MIN_ORDER_FEE = 1.00
        MAX_ORDER_FEE = shares * avg_price * 0.01

        cost = shares * PER_SHARE_FEE
        return min(max(cost, MIN_ORDER_FEE), MAX_ORDER_FEE)
    

class MarketSimulator:

    def __init__(self, slippage_model=IdealFillSlippageModel(), cost_structure=ZeroCostStructure()):

        self.slippage_model = slippage_model
        self.cost_structure = cost_structure

        self.positions = {}
        self.position_PnL = {}
        self.short_lots = {}
        self.long_lots = {}

    def fill_order(self, stock, NBBO, order_qty, timestamp, buy_side=True, cost_to_borrow=0.0):

        """
        timestamp: Unix nanosecond timestamp for simulation time
        """

        avg_price, filled_qty = self.slippage_model.calculate_slippage(NBBO, order_qty, buy_side)
        if filled_qty <= 0:
            return None

        if stock not in self.positions:
            self.positions[stock] = 0
            self.position_PnL[stock] = 0.0
            self.short_lots[stock] = []
            self.long_lots[stock] = [] 

        if buy_side:
            if self.positions[stock] < 0:
                qty_to_cover = min(filled_qty, abs(self.positions[stock]))
                self._cover_short(stock, qty_to_cover, avg_price, timestamp)
                filled_qty -= qty_to_cover
            if filled_qty > 0:
                self.positions[stock] += filled_qty
                self.long_lots[stock].append({
                    "qty": filled_qty,
                    "entry_time": timestamp,
                    "entry_price": avg_price
                })
                self.position_PnL[stock] -= avg_price * filled_qty + self.cost_structure.calculate_cost(filled_qty, avg_price)
        else:
            self.positions[stock] -= filled_qty
            self.short_lots[stock].append({
                "qty": filled_qty,
                "entry_time": timestamp,
                "entry_price": avg_price,
                "borrow_rate": cost_to_borrow
            })
            self.position_PnL[stock] += avg_price * filled_qty - self.cost_structure.calculate_cost(filled_qty, avg_price)

    def _cover_short(self, stock, qty_to_cover, cover_price, timestamp):
        lots = self.short_lots[stock]
        qty_left = qty_to_cover
        while qty_left > 0 and lots:
            lot = lots[0]
            lot_qty = lot["qty"]
            used_qty = min(qty_left, lot_qty)
            holding_days = (timestamp - lot["entry_time"]) / 1e9 / 86400
            borrow_cost = used_qty * lot["entry_price"] * lot["borrow_rate"] * holding_days / 365
            pnl = (lot["entry_price"] - cover_price) * used_qty - borrow_cost
            self.position_PnL[stock] += pnl
            lot["qty"] -= used_qty
            qty_left -= used_qty
            if lot["qty"] == 0:
                lots.pop(0)

    def get_stock_Pnl(self, stock):
        return self.position_PnL.get(stock, 0.0)

    def get_total_PnL(self):
        return sum(self.position_PnL.values())

    def get_stock_unrealized_PnL(self, stock, NBBO):
        position = self.positions.get(stock, 0)
        if position > 0:
            market_price = NBBO.get("bid")
            pnl = sum((market_price - lot["entry_price"]) * lot["qty"] for lot in self.long_lots.get(stock, []))
        elif position < 0:
            market_price = NBBO.get("ask")
            pnl = sum((lot["entry_price"] - market_price) * lot["qty"] for lot in self.short_lots.get(stock, []))
        else:
            pnl = 0.0
        return pnl