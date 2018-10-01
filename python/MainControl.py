import os, sys, glob, logging
from optparse import OptionParser

def fix_path(file_name):
    return os.path.abspath(os.path.normpath(os.path.expanduser(file_name)))

def get_dir_name(file_name):
    return os.path.normpath(os.path.dirname(fix_path(file_name)))

logger = logging.getLogger(__name__)
py_src_dir = get_dir_name(__file__)
sys.path.insert(0, py_src_dir)
sys.path.insert(0, os.path.normpath(py_src_dir+'/../modules/spi'))
sys.path.insert(0, os.path.normpath(py_src_dir+'/../modules/fpga'))
sys.path.insert(0, os.path.normpath(py_src_dir+'/../modules/i2c'))

# files_to_load = ['COController.py', 'FpgaController.py']
files_to_load = ['GuiControl.py']
for ff in files_to_load:
    filename = py_src_dir + '/' + ff
    if not os.path.exists(filename):
        raise ValueError("File: " + filename + " does not exist. Check file existance and permission")
    execfile(filename, globals(), locals())

def main():
    usage = "AD converter demo"
    parser = OptionParser(usage)
    parser.add_option('--gui', '-g', dest="enable_gui", action='store_true', help='Enable GUI display')
    parser.add_option('--log', '-l', dest="logfile_name", default="run.log", help="Sets name of log file. Default=%default")

    (args, dirs) = parser.parse_args()
    try:
        logfile_name = os.path.abspath(fix_path(args.logfile_name))
        log_file = logging.FileHandler(logfile_name)
        log_file.setFormatter(logging.Formatter('%(levelname)-7s [%(asctime)s.%(msecs)03d]: %(name)s - %(message)s', datefmt='%H:%M:%S'))
        logging.getLogger().addHandler(log_file)
        logging.getLogger().setLevel(logging.DEBUG)
    except:
        raise RuntimeError("Failed to open log file: {0}".format(args.logfile_name))

    logger.debug("I am writting to a file")

    if args.enable_gui:
        launch_gui()

if __name__ == '__main__':
    main()