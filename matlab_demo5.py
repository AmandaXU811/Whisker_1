import os
import time
import matlab.engine

MATLAB_START_TIMEOUT = 60  # seconds
PREFER_SHARED_MATLAB = True
MATLAB_QUIT_ON_EXIT = False  # Keep MATLAB alive so async recording can finish
MATLAB_PLOT_START_WAIT = 2.0  # seconds to wait before starting UR5


def _start_matlab_engine():
    if PREFER_SHARED_MATLAB:
        try:
            names = matlab.engine.find_matlab()
            if names:
                return matlab.engine.connect_matlab(names[0]), False
        except Exception:
            pass
    return matlab.engine.start_matlab(), True


def start_demo5_plot(base_dir, do_record=True, name_tag=""):
    eng, matlab_started_here = _start_matlab_engine()
    visualization_dir = os.path.join(base_dir, "Visualization")
    eng.cd(visualization_dir, nargout=0)

    app = eng.App_AllDemos(nargout=1)
    eng.workspace["app"] = app

    eng.eval("app.TabGroup.SelectedTab = app.Demo5Tab; drawnow;", nargout=0)
    eng.eval("try; app.UIFigure.WindowState = 'normal'; app.UIFigure.Position = [50 50 1600 900]; catch; end; drawnow;", nargout=0)

    eng.workspace["record_flag"] = bool(do_record)
    eng.workspace["record_tag"] = str(name_tag)
    future = eng.eval(
        "run_dual_plot(app.Demo5_UIAxes, app.Demo5_UIAxes_2, record_flag, record_tag);",
        nargout=0,
        background=True,
    )

    time.sleep(MATLAB_PLOT_START_WAIT)
    if future.done():
        future.result()
        raise RuntimeError("Demo5 plotting finished too quickly; check MATLAB logs.")

    return eng, matlab_started_here, app, future

