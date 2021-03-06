import matplotlib.pyplot as plt
import numpy as np
from networktables import NetworkTables

wait_time = 0.1
sec_lim = 4
btn = None
paused = False


class NTData:
    def __init__(self, plot_line):
        self.plot_line = plot_line
        self.data_x = []
        self.data_y = []
        self.accum = 0


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


def plot_init(vel_max, sec_max):
    plt.style.use('ggplot')
    plt.ion()
    fg, ax = plt.subplots(2, 2)
    fg.canvas.set_window_title('CheeseWrangler Velocity Grapher')
    plt.tight_layout()

    ax[0, 0].set_title('vX')
    ax[0, 1].set_title('vY')
    ax[1, 0].set_title('vL')
    ax[1, 1].set_title('vR')

    ax[0, 0].set_xlim([-sec_max, sec_max / 5])
    ax[0, 1].set_xlim([-sec_max, sec_max / 5])
    ax[1, 0].set_xlim([-sec_max, sec_max / 5])
    ax[1, 1].set_xlim([-sec_max, sec_max / 5])

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


def btn_callback(event):
    global paused
    paused = not paused
    global btn
    if paused:
        btn.label.set_text('Unpause')
    else:
        btn.label.set_text('Pause')


def setup_textbox(ax, text):
    return ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=10, verticalalignment='top')


def get_all_text_boxes(axs):
    return [
        setup_textbox(axs[0, 0], 0),
        setup_textbox(axs[0, 1], 0),
        setup_textbox(axs[1, 0], 0),
        setup_textbox(axs[1, 1], 0)
    ]


def trapezoid_integral(y_data):
    accum = 0
    for idx in range(len(y_data) - 1):
        accum += (y_data[idx + 1] + y_data[idx]) / 2 * wait_time
    return accum


def main():
    shuffleboard = nt_init()
    fig, axs = plot_init(sec_lim, 5)
    lines = line_init(axs)
    plt.show()
    tbs = get_all_text_boxes(axs)
    b_axes = plt.axes([0.9, 0, 0.1, 0.075])
    p_btn = plt.Button(b_axes, 'Pause')
    p_btn.on_clicked(btn_callback)
    global btn
    btn = p_btn

    math_text = '$\\tau=$%s\n$\\alpha=$%s\n$\\int=$%s'
    time_elapsed = 0
    has_data = False
    ntd = []
    for line in lines:
        ntd.append(NTData(line))
    while True:
        while NetworkTables.isConnected():
            if not has_data:
                print('Connected to NT server')
            has_data = True
            raw_data = nt_get_data(shuffleboard)
            for idx, line in enumerate(lines):
                curr = ntd[idx]
                curr.data_x.append(time_elapsed)
                curr.data_y.append(raw_data[idx])
                if not paused:
                    line.set_data(curr.data_x, curr.data_y)
                    if np.min(curr.data_y) <= line.axes.get_ylim()[0] or np.max(curr.data_y) >= line.axes.get_ylim()[1]:
                        plt.ylim([np.min(curr.data_y) - np.std(curr.data_y), np.max(curr.data_y) + np.std(curr.data_y)])

            if not paused:
                l2r = int(len(lines) / 2)
                accum_min = int(max((time_elapsed - sec_lim) / wait_time, 0))
                for idx in range(l2r):
                    accum = trapezoid_integral(ntd[idx + l2r].data_y[accum_min:-1]) - \
                            trapezoid_integral(ntd[idx].data_y[accum_min:-1])
                    tbs[idx].set_text(math_text % (round(ntd[idx].data_y[-1], 2),
                                                   round(ntd[idx + l2r].data_y[-1], 2),
                                                   round(accum, 2)))
                for r in range(len(axs)):
                    for c in range(len(axs[r])):
                        axs[r][c].set_xlim([time_elapsed - sec_lim, time_elapsed + (sec_lim / 5)])
            time_elapsed += wait_time
            plt.pause(wait_time)
        if has_data:
            print('Connection to NT server lost. Retrying.')
            time_elapsed = 0
            for d in ntd:
                d.data_x = []
                d.data_y = []
            has_data = False
        plt.pause(2)


if __name__ == '__main__':
    main()
