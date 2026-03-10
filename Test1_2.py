from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import matlab.engine
import os
import time

ROBOT_IP = "169.254.93.5"

START_CM = 5
END_CM = 15
STEP_CM = 1

SPEED = 0.08
ACC = 0.25
END_SLEEP = 5

FWD_SIGN = +1   # forward = +X

APP_DIR = os.path.join(os.path.dirname(__file__), "Visualization")
MATLAB_READY_FLAG = os.path.join(APP_DIR, "visualization_ready.flag")

def pose_copy(p):
    return [float(x) for x in p]

def _connect_matlab():
    sessions = matlab.engine.find_matlab()
    if sessions:
        return matlab.engine.connect_matlab(sessions[0])
    return matlab.engine.start_matlab("-desktop")

def launch_visualization_demo5():
    if os.path.exists(MATLAB_READY_FLAG):
        os.remove(MATLAB_READY_FLAG)

    eng = _connect_matlab()
    app_dir_matlab = APP_DIR.replace("\\", "/").replace("'", "''")
    eng.eval(f"cd('{app_dir_matlab}'); addpath('{app_dir_matlab}');", nargout=0)
    eng.eval("disp('Starting App_AllDemos -> Demo5 -> Start');", nargout=0)
    eng.feval("open_demo5_start_v2", nargout=0)
    eng.eval("disp('Visualization ready');", nargout=0)

    start = time.time()
    while time.time() - start < 120:
        if os.path.exists(MATLAB_READY_FLAG):
            return True
        time.sleep(0.5)

    return False

def main():
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)

    try:
        if not rtde_r.isConnected():
            raise RuntimeError("RTDEReceive not connected.")

        left_pose = pose_copy(rtde_r.getActualTCPPose())
        print("Reference pose:", left_pose)

        print("Launching visualization app (demo5/start) ...")
        if not launch_visualization_demo5():
            raise RuntimeError("Visualization app did not signal ready.")

        time.sleep(END_SLEEP)

        for step_cm in range(START_CM, END_CM + 1, STEP_CM):

            step_m = step_cm / 100.0
            print(f"\n--- Move amplitude: {step_cm} cm ---")

            # 1) Move forward
            fwd_pose = pose_copy(left_pose)
            fwd_pose[0] += FWD_SIGN * step_m
            print("Move to:", fwd_pose)
            rtde_c.moveL(fwd_pose, speed=SPEED, acceleration=ACC)

            # 2) Return
            print("Return to:", left_pose)
            rtde_c.moveL(left_pose, speed=SPEED, acceleration=ACC)

            print(f"Sleep {END_SLEEP}s")
            time.sleep(END_SLEEP)

            pose_now = rtde_r.getActualTCPPose()
            print("Current pose:", pose_now)

        print("\nDone.")

    finally:
        try:
            rtde_c.stopScript()
        except:
            pass
        rtde_c.disconnect()
        rtde_r.disconnect()

if __name__ == "__main__":
    main()
