from client import Client
from constants import PORT
import os
import base64
import subprocess
import threading
import time
import shutil

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
            folder_name = f"worker_blend_files/{self.ID}"
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
            folder_name = folder_name.replace("\\", "/")
            if not os.path.exists(folder_name+"/images"):
                os.mkdir(folder_name+"/images")
            # command = f'{blender_path} -b {folder_name}/{file_name} -o {folder_name}/images/ -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a'
            threading.Thread(target=self.send_images, args=(folder_name, start_frame, end_frame)).start()
            subprocess.call(f'"{blender_path}" -b "{folder_name}/{file_name}" -o "{folder_name}/images/" -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a', shell=False)
            # stdout, stderr = process.communicate()
            

            # Check for any errors
            # if return_code != 0:
            #     print(f"Error")
            # else:
            #     print("Render completed successfully.")

            # send result
            # result = {}
            # images_list = os.listdir(folder_name+"/images/")
            # for i in range(len(images_list)):
            #     f = open(f"{folder_name}/images/{images_list[i]}", "rb")
            #     file = f.read()
            #     result[i] = base64.b64encode(file).decode('utf-8')
            #     f.close()
            # for i in range(start_frame, end_frame+1):
            #     f = open(f"{folder_name}/{'0'*len(str(i))}{i}.png", "rb")
            #     file = f.read()
            #     result[i] = file
            #     f.close()
            
            
            # result = message
            # message.pop("message")
            # message["message_type"] = "result"
            # message["message"] = result
            # print(f"[INFO] Sending result for task {task_id}")
            # print(f"[INFO] Acknowledgment sent for task {task_id}")

            # self.send_message(message)
            # print(f"[INFO] Result sent for task {task_id}")

            # result = eval(function_name+"(input_task)")
            # self.send_ack()
            # message["message_type"] = "result"
            # message["message"] = result
            # self.send_message(message)
    
    def send_images(self, folder_name, start_frame, end_frame):
        i=0
        while i < end_frame-start_frame+1:
            images = os.listdir(folder_name+"/images/")
            if len(images) == 0:
                time.sleep(1)
                continue
            try:
                f = open(f"{folder_name}/images/{images[0]}", "rb")
            except:
                time.sleep(1)
                continue
            file = f.read()
            self.send_message({
                "frame": base64.b64encode(file).decode('utf-8'),
                # "frame_num": int(images[0])+start_frame
                "frame_num": i+start_frame
            })
            print(f"[INFO] Sent frame {i+start_frame}")
            i+=1
        # os.remove(f"{folder_name}/images/{images[0]}")
        # os.rmdir(f"{folder_name}/images")
        shutil.rmtree(f"{folder_name}/images")
            
        

if __name__ == "__main__":
    w = Worker("192.168.0.100", PORT)
