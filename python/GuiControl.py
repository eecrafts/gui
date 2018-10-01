import os, sys, re, logging, json
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# Customize logging
# logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class GUPlainTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super(GUPlainTextEditLogger, self).__init__()
        self.widget_ = widget
    def emit(self, record):
        msg = self.format(record)
        self.widget_.appendPlainText(msg)


class GUMatplotDockWidget(QtGui.QDockWidget):
    def __init__(self, parent, name):
        super(GUMatplotDockWidget, self).__init__(parent)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        self.setWindowTitle(name)
        children = parent.findChildren(GUMatplotDockWidget)
        if len(children) > 1:
            parent.tabifyDockWidget(children[0], self)
            self.raise_()


class GUWaveformPlotter(QtGui.QWidget):
    def __init__(self, parent=None):
        super(GUWaveformPlotter, self).__init__()
        self.figure_ = Figure()
        self.canvas_ = FigureCanvas(self.figure_)
        self.canvas_.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.toolbar_ = NavigationToolbar(self.canvas_, self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar_)
        layout.addWidget(self.canvas_)
        self.setLayout(layout)
        self.setFocus()

    def plot(self, wfms):
        pass


class GUMainWindow(QtGui.QMainWindow):
    def __init__(self, main_control=None, parent=None):
        super(GUMainWindow, self).__init__(parent)
        self.main_ctrl_ = main_control
        self.resource_dir_ = os.path.abspath(os.path.normpath(os.path.dirname(os.path.expanduser(__file__))))
        self.resource_dir_ = os.path.join(self.resource_dir_, 'resources')
        self.icon_path_ = os.path.join(self.resource_dir_, 'icons')
        self.resize(800, 600)
        self.menu_ = self._create_menu_bar()
        self.central_widget_ = QtGui.QWidget()
        self.setCentralWidget(self.central_widget_)
        layout = QtGui.QHBoxLayout(self.central_widget_)
        # Add control panel for all the controls
        panel_frame = QtGui.QFrame()
        panel_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.panel_widget_ = self._create_control_panel(panel_frame)
        # Add plotter for waveform display
        log_frame = QtGui.QFrame()
        log_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.plot_widget_ = GUWaveformPlotter()
        h_splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        h_splitter.addWidget(panel_frame)
        h_splitter.addWidget(self.plot_widget_)        
        h_splitter.setSizes([300, 500])

        v_splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        v_splitter.addWidget(h_splitter)
        # Add log console for real time logging
        self.log_console_ = self._add_log_console()
        self.logger_ = logging.getLogger("GUI")
        v_splitter.addWidget(self.log_console_)
        layout.addWidget(v_splitter)
        self.setLayout(layout)
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Plastique'))
        self.setWindowTitle("Demo")

    def _create_menu_bar(self):
        self.menu_bar_ = self.menuBar()
        self.stat_bar_ = self.statusBar()
        self.tool_bar_ = self.addToolBar('toolbar')
        self.stat_bar_.showMessage('Ready')

        # Create File menu    
        file_menu = self.menu_bar_.addMenu("&File")
        new_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/22x22/actions/document-new.png'))
        new_action = QtGui.QAction(new_icon, '&New Project ...', self)
        new_action.setShortcut('Ctrl+n')
        new_action.setStatusTip('Create a new project')
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        self.tool_bar_.addAction(new_action)

        open_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/22x22/actions/document-open.png'))
        open_action = QtGui.QAction(open_icon, '&Open Project ...', self)
        open_action.setShortcut('Ctrl+o')
        open_action.setStatusTip('Open an existing project')
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        self.tool_bar_.addAction(open_action)

        save_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/22x22/actions/document-save.png'))
        save_action = QtGui.QAction(save_icon, '&Save', self)
        save_action.setShortcut('Ctrl+s')
        save_action.setStatusTip('Save project')
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        self.tool_bar_.addAction(save_action)

        save_as_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/22x22/actions/document-save-as.png'))
        save_as_action = QtGui.QAction(save_as_icon, "&Save As ...", self)
        save_as_action.setShortcut("Ctrl+a")
        save_as_action.setStatusTip("Save current project with different name")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)

        # Create menu for uplink
        uplink_menu = self.menu_bar_.addMenu("&Uplink")
        send_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/scalable/actions/system-run-symbolic.svg'))
        send_action = QtGui.QAction(send_icon, 'Send &Command ...', self)
        send_action.setShortcut("Ctrl+C")
        send_action.triggered.connect(self._send_command)
        uplink_menu.addAction(send_action)
        self.tool_bar_.addAction(send_action)

        file_menu.addSeparator()
        exit_icon = QtGui.QIcon(os.path.normpath(self.icon_path_ + '/scalable/actions/system-shutdown-symbolic.svg'))
        exit_action = QtGui.QAction(exit_icon, "&Exit ...", self)
        exit_action.setShortcut("Ctrl+X")
        exit_action.setStatusTip("Quit Application")
        exit_action.triggered.connect(self._quit_application)
        file_menu.addAction(exit_action)
        self.tool_bar_.addSeparator()
        self.tool_bar_.addAction(exit_action)
    
        
    def _new_project(self):
        self.logger_.info('Create a new project')

    def _open_project(self):
        self.logger_.info('open an existing project')

    def _save_project(self):
        self.logger_.info('save an project')

    def _save_project_as(self):
        self.logger_.info('save object into')

    def _quit_application(self):
        self.logger_.info('Quit Application')
        QtCore.QCoreApplication.instance().quit()

    def _send_command(self):
        self.logger_.info('Send command')
        
    def _add_log_console(self):
        console = QtGui.QPlainTextEdit()
        console.setReadOnly(True)
        font = QtGui.QFont()
        font.setFamily(QtCore.QString.fromUtf8("Consolas"))
        font.setPointSize(10)
        console.setFont(font)
        logger = GUPlainTextEditLogger(console)
        logger.setFormatter(logging.Formatter('%(levelname)-7s [%(asctime)s.%(msecs)03d]: %(name)s - %(message)s', datefmt='%H:%M:%S'))
        logging.getLogger().addHandler(logger)
        logging.getLogger().setLevel(logging.DEBUG)
        return console

    def _create_control_panel(self, panel_frame):
        frame_layout = QtGui.QVBoxLayout(panel_frame)

        # Control: on-board / software
        control_group = QtGui.QGroupBox(panel_frame)
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(control_group.sizePolicy().hasHeightForWidth())
        control_group.setSizePolicy(size_policy)
        control_group.setTitle(_translate("MainWindow", "Control", None))
        control_group_layout = QtGui.QHBoxLayout(control_group)
        self.ctrl_on_board_ = QtGui.QRadioButton(control_group)
        self.ctrl_on_board_.setText(_translate("MainWindow", "On-board", None))
        self.ctrl_on_board_.setToolTip('Enables on-board manual control')
        self.ctrl_software_ = QtGui.QRadioButton(control_group)
        self.ctrl_software_.setText(_translate("MainWindow", "Software", None))
        self.ctrl_software_.setToolTip('Enables control through software')
        self.ctrl_software_.setChecked(True)
        control_group_layout.addWidget(self.ctrl_on_board_)
        control_group_layout.addWidget(self.ctrl_software_)
        control_group.raise_()
        frame_layout.addWidget(control_group)

        # Frequency
        freq_layout = QtGui.QHBoxLayout()
        freq_name_label = QtGui.QLabel(panel_frame)
        freq_name_label.setText(_translate("MainWindow", "Frequency", None))
        freq_layout.addWidget(freq_name_label)
        self.freq_editor_ = QtGui.QLineEdit(panel_frame)
        self.freq_editor_.setToolTip('Set operation frequency')
        self.freq_editor_.setText("50")
        self.freq_editor_.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        freq_layout.addWidget(self.freq_editor_)
        freq_unit_label = QtGui.QLabel(panel_frame)
        freq_unit_label.setText(_translate("MainWindow", "MHz", None))
        freq_layout.addWidget(freq_unit_label)
        freq_spacer = QtGui.QSpacerItem(60, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        freq_layout.addItem(freq_spacer)
        frame_layout.addLayout(freq_layout)

        # Calibration
        calibration_group = QtGui.QGroupBox(panel_frame)
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(calibration_group.sizePolicy().hasHeightForWidth())
        calibration_group.setTitle(_translate("MainWindow", "Calibration", None))
        calibration_group.setSizePolicy(size_policy)
        calibration_group_layout = QtGui.QVBoxLayout(calibration_group)
        self.calibr_sar1_ca_ = QtGui.QCheckBox(calibration_group)
        self.calibr_sar1_ca_.setText(_translate("MainWindow", "Calibration SAR1 CA", None))
        self.calibr_sar1_ca_.setChecked(True)
        self.calibr_sar1_ca_.setEnabled(False)
        calibration_group_layout.addWidget(self.calibr_sar1_ca_)
        self.calibr_sar2_cm_ = QtGui.QCheckBox(calibration_group)
        self.calibr_sar2_cm_.setText(_translate("MainWindow", "Calibration SAR2 CM", None))
        self.calibr_sar2_cm_.setChecked(True)
        self.calibr_sar2_cm_.setEnabled(False)
        calibration_group_layout.addWidget(self.calibr_sar2_cm_)
        self.calibr_sar2_ca_ = QtGui.QCheckBox(calibration_group)
        self.calibr_sar2_ca_.setText(_translate("MainWindow", "Calibration SAR2 CA", None))
        calibration_group_layout.addWidget(self.calibr_sar2_ca_)
        self.calibr_sar_ca_ = QtGui.QCheckBox(calibration_group)
        self.calibr_sar_ca_.setText(_translate("MainWindow", "Calibration SAR CA", None))
        calibration_group_layout.addWidget(self.calibr_sar_ca_)
        frame_layout.addWidget(calibration_group)

        # Normal operation
        operation_group = QtGui.QGroupBox(panel_frame)
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(operation_group.sizePolicy().hasHeightForWidth())
        operation_group.setTitle(_translate("MainWindow", "Operation", None))
        operation_group_layout = QtGui.QVBoxLayout(operation_group)
        sample_count_layout = QtGui.QHBoxLayout()
        sample_count_label = QtGui.QLabel(operation_group)
        sample_count_label.setText(_translate("MainWindow", "Sample Counts:", None))
        sample_count_layout.addWidget(sample_count_label)
        self.sample_count_spinner_ = QtGui.QSpinBox(operation_group)
        self.sample_count_spinner_.setMinimum(1)
        self.sample_count_spinner_.setMaximum(511)
        self.sample_count_spinner_.setValue(256)
        sample_count_layout.addWidget(self.sample_count_spinner_)
        sample_count_spacer = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        sample_count_layout.addItem(sample_count_spacer)
        operation_group_layout.addLayout(sample_count_layout)
        sampling_layout = QtGui.QHBoxLayout()
        self.sampling_button_ = QtGui.QPushButton(operation_group)
        self.sampling_button_.setText(_translate("MainWindow", "Start Sampling", None))
        sampling_layout.addWidget(self.sampling_button_)
        sampling_spacer = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        sampling_layout.addItem(sampling_spacer)
        operation_group_layout.addLayout(sampling_layout)
        frame_layout.addWidget(operation_group)
       
        frame_spacer = QtGui.QSpacerItem(60, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        frame_layout.addItem(frame_spacer)

def launch_gui():
    app = QtGui.QApplication(sys.argv)
    gui = GUMainWindow()
    gui.show()
    sys.exit(app.exec_())
