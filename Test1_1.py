from rtde_control import RTDEControlInterface
from rtde_receive import RTDEReceiveInterface
import time
import os
import subprocess
from datetime import datetime
import shutil

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
PRE_UR5_SLEEP = 5  # seconds before starting UR5 loop


def pose_copy(p):
    return [float(x) for x in p]

def _find_ffmpeg():
    hardcoded = r"C:\Users\AMD\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
    if os.path.isfile(hardcoded):
        return hardcoded
    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path
    env_path = os.environ.get("FFMPEG_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path
    return None



def main():
    eng = None
    matlab_started_here = False
    plot_future = None
    ffmpeg_proc = None
    stop_flag_path = os.path.join(os.path.dirname(__file__), "Visualization", "stop_recording.flag")
    rtde_c = RTDEControlInterface(ROBOT_IP)
    rtde_r = RTDEReceiveInterface(ROBOT_IP)

    try:
        if not rtde_r.isConnected():
            raise RuntimeError("RTDEReceive not connected.")
        print("Starting MATLAB App_AllDemos and Demo5 plotting...")
        if os.path.exists(stop_flag_path):
            os.remove(stop_flag_path)
        record_input = input("Record data? (y/n): ").strip().lower()
        do_record = record_input in ("y", "yes")
        name_tag = ""
        if do_record:
            user_tag = input("Enter name after 'test_' (e.g. a_b_c): ").strip()
            if user_tag.startswith("test_"):
                name_tag = user_tag
            elif user_tag:
                name_tag = "test_" + user_tag
            else:
                name_tag = "test_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        video_input = input("Record Demo5 video via ffmpeg? (y/n): ").strip().lower()
        do_video = video_input in ("y", "yes")

        eng, matlab_started_here, _app, plot_future = matlab_demo5.start_demo5_plot(
            os.path.dirname(__file__),
            do_record=do_record,
            name_tag=name_tag,
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
        if do_video:
            video_dir = os.path.join(os.path.dirname(__file__), "Visualization", "video")
            os.makedirs(video_dir, exist_ok=True)
            if name_tag:
                video_name = f"reconstruction_{name_tag}"
            else:
                video_name = f"reconstruction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            video_path = os.path.join(video_dir, video_name + ".mp4")
            video_tmp_path = os.path.join(video_dir, video_name + ".mkv")
            ffmpeg_path = _find_ffmpeg()
            if not ffmpeg_path:
                print("ffmpeg not found. Set FFMPEG_PATH or install ffmpeg in PATH.")
            else:
                ffmpeg_cmd = [
                    ffmpeg_path,
                    "-y",
                    "-f",
                    "gdigrab",
                    "-framerate",
                    "30",
                    "-i",
                    'title=MATLAB App',
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "15",
                    "-pix_fmt",
                    "yuv420p",
                    video_tmp_path,
                ]
                try:
                    ffmpeg_proc = subprocess.Popen(
                        ffmpeg_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print(f"Demo5 video recording started: {video_tmp_path}")
                except Exception as e:
                    print(f"ffmpeg failed to start: {e}")

        time.sleep(PRE_UR5_SLEEP)
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
            if ffmpeg_proc is not None and ffmpeg_proc.stdin:
                ffmpeg_proc.stdin.write(b"q\n")
                ffmpeg_proc.stdin.flush()
                ffmpeg_proc.wait(timeout=10)
        except Exception:
            pass
        try:
            if ffmpeg_proc is not None:
                ffmpeg_path = _find_ffmpeg()
                if ffmpeg_path and "video_tmp_path" in locals() and os.path.isfile(video_tmp_path):
                    remux_cmd = [
                        ffmpeg_path,
                        "-y",
                        "-i",
                        video_tmp_path,
                        "-c",
                        "copy",
                        video_path,
                    ]
                    subprocess.run(remux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    try:
                        os.remove(video_tmp_path)
                    except Exception:
                        pass
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
