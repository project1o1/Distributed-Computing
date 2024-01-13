from client import Client
from constants import PORT
import os
import base64
import subprocess
import threading

blender_path = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
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

    def start_message_loop(self):
        while True:
            user_input = input("Enter message to send (or type 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            self.send_message(user_input)
    
    def start_task_loop(self):
        while True:
            message = self.receive_message()
            if message is None:
                break
            print("[INFO] Blender file received")
            # print(f"[INFO] Message received: {message}")
            task = message["message"]
            task_id = task["task_id"]
            file_name = task["file_name"]
            file = task["file"]
            file = base64.b64decode(file)
            start_frame = task["start_frame"]
            end_frame = task["end_frame"]
            # create folder
            folder_name = f"worker_blend_files/{task_id}"
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            
            print(f"[INFO] Received task {task_id} with file {file_name} from frame {start_frame} to {end_frame}")
            # print(task)
            # write file
            f = open(f"{folder_name}/{file_name}", "wb")
            f.write(file)
            f.close()
            print(f"[INFO] File {file_name} written to {folder_name}")          

            
            # self.send_ack()
            
            # execute blender
            # output_path = os.path.join(folder_name, f'frame_{frame_num:04d}')
            folder_name = os.path.abspath(folder_name)
            # command = f'{blender_path} -b {folder_name}/{file_name} -o {folder_name}/images/ -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a'
            threading.Thread(target=self.send_images, args=(folder_name, start_frame, end_frame)).start()
            subprocess.call(f'"{blender_path}" -b "{folder_name}/{file_name}" -o "{folder_name}/images/" -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a', shell=False)

    
    def send_images(self, folder_name, start_frame, end_frame):
        i=0
        while i < end_frame-start_frame+1:
            images = os.listdir(folder_name+"/images/")
            if len(images) == 0:
                continue
            f = open(f"{folder_name}/images/{images[0]}", "rb")
            file = f.read()
            self.send_message({
                "frame": base64.b64encode(file).decode('utf-8'),
                # "frame_num": int(images[0])+start_frame
                "frame_num": i+start_frame
            })
            os.remove(f"{folder_name}/images/{images[0]}")
            i+=1
            print(f"[INFO] Sent frame {i}")

if __name__ == "__main__":
    w = Worker("192.168.0.101", PORT)
