import matplotlib.pyplot as plt

class Grapher:

    def __init__(self):

        self.NBBOs = []
        self.positions = []
        self.pnls = []

    def add_data(self, NBBO, position, pnl):

        self.NBBOs.append(NBBO)
        self.positions.append(position)
        self.pnls.append(pnl)

    def show_plot(self):

        fig, ax1 = plt.subplots()

        ax1.set_xlabel("Time")
        ax1.set_ylabel('NBBO', color='tab:blue')
        ax1.plot(self.NBBOs, color='tab:blue', label='NBBO')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Position / PnL', color='tab:red')
        ax2.plot(self.positions, color='tab:red', label='Position')
        ax2.plot(self.pnls, color='tab:green', label='PnL')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        fig.tight_layout()
        plt.title(title)
        plt.show()