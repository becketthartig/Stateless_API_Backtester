class SlippageModel:
    
    """
    Base class for slippage models
    Other models should inherit from this class and implement the calculate_slippage method
    """

    def calculate_slippage(self, NBBO, order_qty, buy_side=True):

        """
        NBBO: (dict) NBBO from interface.MarketSample
        order_qty: (int) quantity of shares to fill
        buy_side: (bool) True for buy orders, False for sell orders
        """

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
    Other cost structures should inherit from this class and implement the calculate_cost method
    """

    def calculate_cost(self, shares, avg_price):

        """
        shares: (int) number of shares in the order
        avg_price: (float) average price of the order from slippage model
        """

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

        """
        Any new models/structures made should inherit from the classes above.
        slippage_model: (SlippageModel) instance of a slippage model
        cost_structure: (CostStructure) instance of a cost structure
        """

        self.slippage_model = slippage_model
        self.cost_structure = cost_structure

        self.positions = {}
        self.position_PnL = {}
        self.short_lots = {}
        self.long_lots = {}

    def fill_order(self, stock, NBBO, order_qty, timestamp, buy_side=True, cost_to_borrow=0.0):

        """
        Fills an order for the given stock internally, you should
        already know what your order is by implementing a Strategy.
        This handles you position and Pnl as a common string across states.
        Accounts for slippage, commision, and borrow costs for shorts currently.

        Parameters:
        stock: (str) stock ticker symbol
        NBBO: (dict) current NBBO from interface.MarketSample
        order_qty: (int) quantity of shares to fill
        timestamp: (int) Unix nanosecond timestamp for simulation time
        buy_side: (bool) True for buy orders, False for sell orders
        cost_to_borrow: (float) cost to borrow shares for short selling, default is 0.0
        """

        avg_price, filled_qty = self.slippage_model.calculate_slippage(NBBO, order_qty, buy_side)
        if filled_qty <= 0:
            return None
        total_qty = filled_qty

        if stock not in self.positions:
            self.positions[stock] = 0
            self.position_PnL[stock] = 0.0
            self.short_lots[stock] = []
            self.long_lots[stock] = [] 

        if buy_side:
            if self.positions[stock] < 0:
                qty_to_cover = min(filled_qty, -self.positions[stock])
                self._cover_short(stock, qty_to_cover, avg_price, timestamp)
                filled_qty -= qty_to_cover
            self.positions[stock] += total_qty
            if filled_qty > 0:
                self.long_lots[stock].append({
                    "qty": filled_qty,
                    "entry_time": timestamp,
                    "entry_price": avg_price
                })
            self.position_PnL[stock] -= self.cost_structure.calculate_cost(total_qty, avg_price)
        else:
            if self.positions[stock] > 0:
                qty_to_cover = min(filled_qty, self.positions[stock])
                self._sell_long(stock, qty_to_cover, avg_price, timestamp)
                filled_qty -= qty_to_cover
            self.positions[stock] -= total_qty
            if filled_qty > 0:
                self.short_lots[stock].append({
                    "qty": filled_qty,
                    "entry_time": timestamp,
                    "entry_price": avg_price,
                    "borrow_rate": cost_to_borrow
                })
            self.position_PnL[stock] -= self.cost_structure.calculate_cost(total_qty, avg_price)

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

    def _sell_long(self, stock, qty_to_sell, sell_price, timestamp):
        lots = self.long_lots[stock]
        qty_left = qty_to_sell
        while qty_left > 0 and lots:
            lot = lots[0]
            lot_qty = lot["qty"]
            used_qty = min(qty_left, lot_qty)
            pnl = (sell_price - lot["entry_price"]) * used_qty
            self.position_PnL[stock] += pnl
            lot["qty"] -= used_qty
            qty_left -= used_qty
            if lot["qty"] == 0:
                lots.pop(0)

    def get_stock_Pnl(self, stock):
        """
        Returns the realized PnL for a given stock
        stock: (str) stock ticker symbol
        """
        return self.position_PnL.get(stock, 0.0)

    def get_all_PnL(self):
        """
        Returns the total realized PnL across all stocks
        """
        return sum(self.position_PnL.values())

    def get_stock_unrealized_PnL(self, stock, NBBO):
        """
        Returns the unrealized PnL for a given stock based on current NBBO
        stock: (str) stock ticker symbol
        NBBO: (dict) current NBBO from interface.MarketSample
        """
        market_bid = NBBO.get("bid", 0)
        market_ask = NBBO.get("ask", 0)
        unrealized = 0.0

        for lot in self.long_lots.get(stock, []):
            unrealized += (market_bid - lot["entry_price"]) * lot["qty"]
            
        for lot in self.short_lots.get(stock, []):
            unrealized += (lot["entry_price"] - market_ask) * lot["qty"]

        return unrealized
    
    def get_equity_curve_sample(self, stock, NBBO):
        """
        Returns the total PnL (realized + unrealized) for a given stock
        stock: (str) stock ticker symbol
        NBBO: (dict) current NBBO from interface.MarketSample
        """
        return self.position_PnL.get(stock, 0) + self.get_stock_unrealized_PnL(stock, NBBO)
