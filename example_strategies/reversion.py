class RangeBound:

    """
    Most basic reversion strategy where stock is assumed to be range
    bound with a stable mean and devaiation from the mean. 
    Purely an example.
    """

    def __init__(self, mean, deviation, max_allowed_position=100):

        self.mean = mean
        self.deviation = deviation
        self.max_allowed_position = max_allowed_position

    def get_order(self, NBBO, current_position):

        """
        Strategies to implement stateless get order function.
        This function buys or sells the max allowed.
        NBBO: (dict) NBBO from interface.MarketSample
        current_position: (int) current position in the stock
        """

        order_qty = 0
        buy_side = True
        
        midpoint = (NBBO.get("bid") + NBBO.get("ask")) / 2

        if midpoint > self.mean + self.deviation:
            order_qty = current_position + self.max_allowed_position
            buy_side = False
        elif midpoint < self.mean - self.deviation:
            order_qty = abs(current_position - self.max_allowed_position)

        return order_qty, buy_side