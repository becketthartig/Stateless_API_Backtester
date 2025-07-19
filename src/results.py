import matplotlib.pyplot as plt

class Grapher:

    def __init__(self):

        self.timestamps = []
        self.NBBOs = []
        self.positions = []
        self.pnls = []

    def add_data(self, timestamp, NBBO, position, pnl):

        self.timestamps.append(timestamp)
        self.NBBOs.append(NBBO)
        self.positions.append(position)
        self.pnls.append(pnl)

    def show_plot(self, title="Simulation Results"):

        fig, axs = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

        bids = [nbbo[0] for nbbo in self.NBBOs]
        asks = [nbbo[1] for nbbo in self.NBBOs]

        axs[0].plot(self.timestamps, bids, color='tab:blue', label='Bid')
        axs[0].plot(self.timestamps, asks, color='tab:orange', label='Ask')
        axs[0].set_ylabel('NBBO')
        axs[0].legend()
        axs[0].set_title('Bid/Ask')

        axs[1].plot(self.timestamps, self.positions, color='tab:red', label='Position')
        axs[1].set_ylabel('Position')
        axs[1].legend()
        axs[1].set_title('Position')

        axs[2].plot(self.timestamps, self.pnls, color='tab:green', label='PnL')
        axs[2].set_ylabel('PnL')
        axs[2].legend()
        axs[2].set_title('PnL')
        axs[2].set_xlabel('Time')

        fig.suptitle(title)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()