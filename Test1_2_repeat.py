from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import time

ROBOT_IP = "169.254.93.5"

N_REPEAT = 10
STEP_X = 0.05      # 5 cm
SPEED = 0.04
ACC = 0.25
END_SLEEP = 5

# forward = +X, backward = -X
FWD_SIGN = +1

# -------- 固定起始点 --------
LEFT_POSE = [
    0.6404105100520994,
    -0.24395298756198547,
    0.1688309048140903,
    1.4275485322852548,
    2.1375976791037736,
    -0.896971807487414
]

def pose_copy(p):
    return [float(x) for x in p]

def main():
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)

    try:
        if not rtde_r.isConnected():
            raise RuntimeError("RTDEReceive not connected.")

        print("Moving to reference pose...")
        rtde_c.moveL(LEFT_POSE, speed=SPEED, acceleration=ACC)

        left_pose = pose_copy(LEFT_POSE)
        print("Reference pose reached:", left_pose)

        for k in range(1, N_REPEAT + 1):
            print(f"\n--- Iteration {k}/{N_REPEAT} ---")

            # 1) Move forward/back 5 cm
            fwd_pose = pose_copy(left_pose)
            fwd_pose[0] += FWD_SIGN * STEP_X
            print("Move to:", fwd_pose)
            rtde_c.moveL(fwd_pose, speed=SPEED, acceleration=ACC)

            # 2) Return to reference pose
            print("Return to:", left_pose)
            rtde_c.moveL(left_pose, speed=SPEED, acceleration=ACC)

            # 3) Sleep
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
