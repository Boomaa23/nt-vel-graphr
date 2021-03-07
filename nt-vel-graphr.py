import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import networktables

wait_time = 0.1
sec_lim = 6
math_text = '$\\tau=$%s\n$\\alpha=$%s\n$\\int=$%s'


class NTData:
    def __init__(self, plot_line):
        self.plot_line = plot_line
        self.data_x = []
        self.data_y = []
        self.accum = 0


class GraphHelper:
    def __init__(self):
        self.shuffleboard = nt_init()
        self.fig, self.axs = plot_init(sec_lim, 5)
        self.vel_lines, self.pos_lines = line_init(self.axs)
        self.btn = plt.Button(plt.axes([0.9, 0, 0.1, 0.075]), 'Pause')
        self.btn.on_clicked(self.btn_callback)
        self.tbs = get_all_text_boxes(self.axs)

        self.vel_ntd = []
        self.pos_ntd = []
        for line in self.vel_lines:
            self.vel_ntd.append(NTData(line))
        for line in self.pos_lines:
            self.pos_ntd.append(NTData(line))
        # Have to keep this var for graph to animate
        self.anim = animation.FuncAnimation(self.fig, self.check_animate, interval=wait_time * 1000)

        self.paused = False
        self.time_elapsed = 0
        self.has_data = False
        plt.show()
        plt.pause(0)

    def nt_get_data(self):
        pt_tab = self.shuffleboard.getSubTable('PathTracer')
        dt_tab = self.shuffleboard.getSubTable('Drive Train')
        return (
            [
                pt_tab.getValue('vX', 0),
                pt_tab.getValue('vY', 0),
                pt_tab.getValue('vL', 0),
                pt_tab.getValue('vR', 0),
                dt_tab.getValue('XVel', 0),
                dt_tab.getValue('YVel', 0),
                dt_tab.getValue('Left Vel', 0),
                dt_tab.getValue('Right Vel', 0)
            ],
            [
                pt_tab.getValue('pX', 0),
                pt_tab.getValue('pY', 0),
                pt_tab.getValue('pXA', 0),
                pt_tab.getValue('pYA', 0),
            ]
        )

    def btn_callback(self, event):
        self.paused = not self.paused
        if self.paused:
            self.btn.label.set_text('Unpause')
        else:
            self.btn.label.set_text('Pause')

    def check_animate(self, frame):
        if networktables.NetworkTables.isConnected():
            if not self.has_data:
                print('Connected to NT server')
            self.animate()
        elif self.has_data:
            print('Connection to NT server lost. Retrying.')
            self.time_elapsed = 0
            for d in self.vel_ntd:
                d.data_x = []
                d.data_y = []
            for d in self.pos_ntd:
                d.data_x = []
                d.data_y = []
            self.has_data = False

    def animate(self):
        self.has_data = True
        vel_data, pos_data = self.nt_get_data()
        for idx, line in enumerate(self.vel_lines):
            curr_ntd = self.vel_ntd[idx]
            curr_ntd.data_x.append(self.time_elapsed)
            curr_ntd.data_y.append(vel_data[idx])
            self.set_and_resize(curr_ntd)

        loop_idx = 0
        for curr_ntd in self.pos_ntd:
            curr_ntd.data_x.append(pos_data[loop_idx])
            curr_ntd.data_y.append(pos_data[loop_idx + 1])
            self.set_and_resize(curr_ntd, True)
            loop_idx += 2

        if not self.paused:
            l2r = int(len(self.vel_lines) / 2)
            accum_min = int(max((self.time_elapsed - sec_lim) / wait_time, 0))
            for idx in range(l2r):
                # accum = trapezoid_integral(self.vel_ntd[idx + l2r].data_y[accum_min:-1]) - \
                accum = trapezoid_integral(self.vel_ntd[idx].data_y[accum_min:-1])
                self.tbs[idx].set_text(math_text % (round(self.vel_ntd[idx].data_y[-1], 3),
                                                    round(self.vel_ntd[idx + l2r].data_y[-1], 3),
                                                    round(accum, 3)))
            for r in range(2):
                for c in range(2):
                    self.axs[r][c].set_xlim([self.time_elapsed - sec_lim, self.time_elapsed + (sec_lim / 5)])

            if self.shuffleboard.getSubTable('PathTracer').getValue('ptReset', False):
                for ntd in self.pos_ntd:
                    ntd.data_x.clear()
                    ntd.data_y.clear()
        self.time_elapsed += wait_time

    def set_and_resize(self, curr, resize_x=False):
        if not self.paused:
            curr.plot_line.set_data(curr.data_x, curr.data_y)
            if np.min(curr.data_y) <= curr.plot_line.axes.get_ylim()[0] or np.max(curr.data_y) >= \
                    curr.plot_line.axes.get_ylim()[1]:
                curr.plot_line.axes.set_ylim(
                    [np.min(curr.data_y) - np.std(curr.data_y), np.max(curr.data_y) + np.std(curr.data_y)])
            if resize_x:
                if np.min(curr.data_x) <= curr.plot_line.axes.get_xlim()[0] or np.max(curr.data_x) >= \
                        curr.plot_line.axes.get_xlim()[1]:
                    curr.plot_line.axes.set_xlim(
                        [np.min(curr.data_x) - np.std(curr.data_x), np.max(curr.data_x) + np.std(curr.data_x)])


def nt_init():
    networktables.NetworkTables.initialize('127.0.0.1')
    print('NT client initialized')
    return networktables.NetworkTables.getTable('Shuffleboard')


def plot_init(vel_max, sec_max):
    plt.style.use('ggplot')
    plt.ion()
    fg, ax = plt.subplots(2, 3, figsize=(10, 6))
    fg.canvas.set_window_title('CheeseWrangler Velocity Grapher')
    plt.tight_layout()

    ax[0, 0].set_title('vX')
    ax[0, 1].set_title('vY')
    ax[1, 0].set_title('vL')
    ax[1, 1].set_title('vR')
    ax[0, 2].set_title('Pos')

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

    lpt, = axs[0, 2].plot(0, 0, color=primary_color)
    lpa, = axs[0, 2].plot(0, 0, color=alt_color)
    print('Lines initialized')
    return [lxt, lyt, llt, lrt, lxa, lya, lla, lra], [lpt, lpa]


def setup_textbox(ax, text):
    return ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=10, verticalalignment='top')


def get_all_text_boxes(axs):
    return [
        setup_textbox(axs[0, 0], 0),
        setup_textbox(axs[0, 1], 0),
        setup_textbox(axs[1, 0], 0),
        setup_textbox(axs[1, 1], 0),
    ]


def trapezoid_integral(y_data):
    accum = 0
    for idx in range(len(y_data) - 1):
        accum += (y_data[idx + 1] + y_data[idx]) / 2 * wait_time
    return accum


if __name__ == '__main__':
    g = GraphHelper()
