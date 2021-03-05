import matplotlib.pyplot as plt
import numpy as np
from networktables import NetworkTables
import time


class NTData:
    def __init__(self, plot_line):
        self.plot_line = plot_line
        self.data_x = []
        self.data_y = []


def nt_init():
    NetworkTables.initialize('127.0.0.1')
    print('NT client initialized')
    return NetworkTables.getTable('Shuffleboard')


def nt_get_data(shuffleboard):
    pt_tab = shuffleboard.getSubTable('PathTracer')
    dt_tab = shuffleboard.getSubTable('Drive Train')
    return [
        pt_tab.getValue('vX', 0),
        pt_tab.getValue('vY', 0),
        pt_tab.getValue('vL', 0),
        pt_tab.getValue('vR', 0),
        dt_tab.getValue('XVel', 0),
        dt_tab.getValue('YVel', 0),
        dt_tab.getValue('Left Vel', 0),
        dt_tab.getValue('Right Vel', 0)
    ]


def plot_init(vel_max=4, sec_max=5):
    plt.style.use('ggplot')
    plt.ion()
    fg, ax = plt.subplots(2, 2)
    plt.tight_layout()

    ax[0, 0].set_title('vX')
    ax[0, 1].set_title('vY')
    ax[1, 0].set_title('vL')
    ax[1, 1].set_title('vR')

    ax[0, 0].set_xlim([-sec_max, sec_max])
    ax[0, 1].set_xlim([-sec_max, sec_max])
    ax[1, 0].set_xlim([-sec_max, sec_max])
    ax[1, 1].set_xlim([-sec_max, sec_max])
    ax[0, 0].set_ylim([-vel_max, vel_max])
    ax[0, 1].set_ylim([-vel_max, vel_max])
    ax[1, 0].set_ylim([-vel_max, vel_max])
    ax[1, 1].set_ylim([-vel_max, vel_max])
    print('Plot initialized')
    return fg, ax


def line_init(axs, primary_color='green', alt_color='red'):
    lxt, = axs[0, 0].plot(0, 0, color=primary_color)
    lyt, = axs[0, 1].plot(0, 0, color=primary_color)
    llt, = axs[1, 0].plot(0, 0, color=primary_color)
    lrt, = axs[1, 1].plot(0, 0, color=primary_color)

    lxa, = axs[0, 0].plot(0, 0, color=alt_color)
    lya, = axs[0, 1].plot(0, 0, color=alt_color)
    lla, = axs[1, 0].plot(0, 0, color=alt_color)
    lra, = axs[1, 1].plot(0, 0, color=alt_color)
    print('Lines initialized')
    return [lxt, lyt, llt, lrt, lxa, lya, lla, lra]


def main():
    shuffleboard = nt_init()
    fig, axs = plot_init()
    lines = line_init(axs)
    plt.show()

    wait_time = 0.1
    time_elapsed = 0

    ntd = []
    for line in lines:
        ntd.append(NTData(line))
    while True:
        while NetworkTables.isConnected():
            raw_data = nt_get_data(shuffleboard)
            for idx, line in enumerate(lines):
                curr = ntd[idx]
                curr.data_x.append(time_elapsed)
                curr.data_y.append(raw_data[idx])
                line.set_data(curr.data_x, curr.data_y)
                if np.min(curr.data_y) <= line.axes.get_ylim()[0] or np.max(curr.data_y) >= line.axes.get_ylim()[1]:
                    plt.ylim([np.min(curr.data_y) - np.std(curr.data_y), np.max(curr.data_y) + np.std(curr.data_y)])
            for r in range(len(axs)):
                for c in range(len(axs[r])):
                    axis = axs[r][c]
                    x_clim = axis.get_xlim()
                    axis.set_xlim([x_clim[0] + wait_time, x_clim[1] + wait_time])
            time_elapsed += wait_time
            plt.pause(wait_time)
        time.sleep(4)


if __name__ == '__main__':
    main()
