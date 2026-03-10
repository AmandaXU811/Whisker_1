from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import time
import os
import subprocess

import matlab_demo5

ROBOT_IP = "169.254.93.5"

# -------- loop params --------
N_REPEAT = 3
STEP_X = 0.00      # 5 cm forward/back (meters)
LIFT_Z = 0.02      # press depth / lift height relative to left_up (meters)

SPEED = 0.04       # slow (half)
ACC = 0.25

# UR base: X forward, Y left, Z up
FWD_SIGN = +1      # set -1 to test backward

END_UP_SLEEP = 5   # seconds at end of each loop (at left_up)
MATLAB_QUIT_ON_EXIT = matlab_demo5.MATLAB_QUIT_ON_EXIT


def pose_copy(p):
    return [float(x) for x in p]



def main():
    eng = None
    matlab_started_here = False
    plot_future = None
    stop_flag_path = os.path.join(os.path.dirname(__file__), "Visualization", "stop_recording.flag")
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)

    try:
        if not rtde_r.isConnected():
            raise RuntimeError("RTDEReceive not connected.")
        print("Starting MATLAB App_AllDemos and Demo5 plotting...")
        if os.path.exists(stop_flag_path):
            os.remove(stop_flag_path)
        eng, matlab_started_here, _app, plot_future = matlab_demo5.start_demo5_plot(
            os.path.dirname(__file__)
        )
        print("Demo5 plotting started. Proceeding with UR5.")
        # Define left_up as CURRENT pose (no initial up/down move)
        print("Define left_up as CURRENT pose (no initial up/down move)")
        left_up = pose_copy(rtde_r.getActualTCPPose())
        left_down = pose_copy(left_up)
        left_down[2] -= LIFT_Z
        current_pose = rtde_r.getActualTCPPose()
        print("Current TCP pose:", current_pose)

        print("Reference left_up (current):", left_up)
        print("Reference left_down (left_up - LIFT_Z):", left_down)
        time.sleep(10)
        for k in range(1, N_REPEAT + 1):
            print(f"\n--- Iteration {k}/{N_REPEAT} ---")

            # 1) Down from left_up to left_down
            print("Down to left_down:", left_down)
            rtde_c.moveL(left_down, speed=SPEED, acceleration=ACC)

            # 2) Move forward/back 5 cm at down height
            fwd_down = pose_copy(left_down)
            fwd_down[0] += FWD_SIGN * STEP_X
            print("Move to fwd_down:", fwd_down)
            rtde_c.moveL(fwd_down, speed=SPEED, acceleration=ACC)

            # 3) Lift up at forward/back position (back to same Z as left_up)
            fwd_up = pose_copy(fwd_down)
            fwd_up[2] += LIFT_Z
            print("Lift to fwd_up:", fwd_up)
            rtde_c.moveL(fwd_up, speed=SPEED, acceleration=ACC)

            # 4) Return to left_up (end loop UP)
            print("Return to left_up:", left_up)
            rtde_c.moveL(left_up, speed=SPEED, acceleration=ACC)

            # 5) Sleep at end of loop
            print(f"End of loop {k}: sleep {END_UP_SLEEP}s at left_up")
            time.sleep(END_UP_SLEEP)

        print("\nDone. Robot remains at left_up.")

    finally:
        try:
            with open(stop_flag_path, "w", encoding="ascii") as f:
                f.write("stop")
        except Exception:
            pass
        try:
            rtde_c.stopScript()
        except Exception:
            pass
        try:
            rtde_c.disconnect()
        except Exception:
            pass
        try:
            rtde_r.disconnect()
        except Exception:
            pass
        try:
            if eng is not None:
                if matlab_started_here and MATLAB_QUIT_ON_EXIT:
                    eng.quit(nargout=0)
        except Exception:
            pass

if __name__ == "__main__":
    main()
