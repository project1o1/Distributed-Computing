from client import Client
from constants import PORT
import os
import base64
import subprocess
import threading
import time
import shutil

# Blender path for Mac
blender_path = "/Applications/Blender.app/Contents/MacOS/Blender"
output_format = "PNG"

class Worker(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "worker"
        self.socket.connect((self.IP, self.port))

        if not os.path.exists("worker_blend_files"):
            os.mkdir("worker_blend_files")

        self.send_message(self.type)
        self.send_message(self.ID)
        print(f"[INFO] Client {self.ID} connected to server")
        self.start_task_loop()

    def start_task_loop(self):
        while True:
            print("[DEBUG] Waiting for task...")
            message = self.receive_message()
            if message is None:
                print("[ERROR] No message received. Exiting worker loop.")
                break

            print("[INFO] Blender file received")

            task = message["message"]
            task_id = task["task_id"]
            file_name = task["file_name"]
            file = base64.b64decode(task["file"])
            start_frame = task["start_frame"]
            end_frame = task["end_frame"]
            fps = task["fps"]

            # Create worker folder
            folder_name = os.path.abspath(f"worker_blend_files/{self.ID}")
            os.makedirs(folder_name, exist_ok=True)

            print(f"[INFO] Received task {task_id} with file {file_name} from frame {start_frame} to {end_frame}")

            # Save Blender file
            file_path = os.path.join(folder_name, file_name)
            with open(file_path, "wb") as f:
                f.write(file)
            print(f"[INFO] File {file_name} written to {folder_name}")

            # Ensure images directory exists
            images_folder = os.path.join(folder_name, "images")
            os.makedirs(images_folder, exist_ok=True)

            # Start thread to send images while rendering
            image_thread = threading.Thread(target=self.send_images, args=(images_folder, start_frame, end_frame, fps))
            image_thread.start()

            # Run Blender rendering command
            log_file = os.path.join(folder_name, "blender_log.txt")
            command = [
                blender_path,
                "-b", file_path,
                "-o", os.path.join(images_folder, ""),
                "-F", output_format,
                "-x", "1",
                "-s", str(start_frame),
                "-e", str(end_frame),
                "-a"
            ]
            print(f"[DEBUG] Running command: {' '.join(command)}")

            # Run Blender and capture output
            with open(log_file, "w") as log:
                result = subprocess.run(command, stdout=log, stderr=log, text=True)

            # Print result if Blender failed
            if result.returncode != 0:
                print(f"[ERROR] Blender process failed. Check log file at {log_file}")

            image_thread.join()
            print(f"[INFO] Task {task_id} completed.")

    def send_images(self, folder_name, start_frame, end_frame, fps):
        i = 0
        while i < (end_frame - start_frame + 1):
            images = sorted(os.listdir(folder_name))  # Ensure correct frame order
            if not images:
                time.sleep(2)  # Increased sleep time to avoid excessive CPU usage
                continue
            try:
                file_path = os.path.join(folder_name, images[0])
                with open(file_path, "rb") as f:
                    file_data = f.read()
                os.remove(file_path)
            except FileNotFoundError:
                time.sleep(2)
                continue

            self.send_message({
                "frame": base64.b64encode(file_data).decode("utf-8"),
                "frame_num": int(images[0].split(".")[0]),
                "fps": fps
            })
            print(f"[INFO] Sent frame {int(images[0].split('.')[0])}")
            i += 1

if __name__ == "__main__":
    w = Worker("127.0.0.1", PORT)
