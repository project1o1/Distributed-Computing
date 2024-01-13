from client import Client
from constants import PORT
import os
import base64
import subprocess

blender_path = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
output_format = "PNG"

class Worker(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "worker"
        self.socket.connect((self.IP, self.port))
        
        if not os.path.exists("worker_blend_files"):
            os.mkdir("worker_blend_files")

        if self.wait_for_ack(expected_ack="CONNECTED"):
            self.send_message(self.type)
            if self.wait_for_ack():
                self.send_message(self.ID)
                if self.wait_for_ack():
                    print(f"[INFO] Client {self.ID} connected to server")
                    # self.start_message_loop()
                    self.start_task_loop()
                else:
                    print(f"[ERROR] Failed to connect to server")
                    exit(1)
            else:
                print(f"[ERROR] Failed to connect to server")
                exit(1)
        else:
            print(f"[ERROR] Failed to connect to server")
            exit(1)

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

            
            self.send_ack()

            # execute blender
            # output_path = os.path.join(folder_name, f'frame_{frame_num:04d}')
            folder_name = os.path.abspath(folder_name)
            # command = f'{blender_path} -b {folder_name}/{file_name} -o {folder_name}/images/ -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a'
            subprocess.call(f'"{blender_path}" -b "{folder_name}/{file_name}" -o "{folder_name}/images/" -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a', shell=True)
            # stdout, stderr = process.communicate()

            # Check for any errors
            # if return_code != 0:
            #     print(f"Error")
            # else:
            #     print("Render completed successfully.")

            # send result
            result = {}
            images_list = os.listdir(folder_name+"/images/")
            for i in range(len(images_list)):
                f = open(f"{folder_name}/images/{images_list[i]}", "rb")
                file = f.read()
                result[i] = base64.b64encode(file).decode('utf-8')
                f.close()
            # for i in range(start_frame, end_frame+1):
            #     f = open(f"{folder_name}/{'0'*len(str(i))}{i}.png", "rb")
            #     file = f.read()
            #     result[i] = file
            #     f.close()
            
            
            # result = message
            message.pop("message")
            message["message_type"] = "result"
            message["message"] = result
            # print(f"[INFO] Sending result for task {task_id}")
            # print(f"[INFO] Acknowledgment sent for task {task_id}")

            self.send_message(message)
            # print(f"[INFO] Result sent for task {task_id}")

            # result = eval(function_name+"(input_task)")
            # self.send_ack()
            # message["message_type"] = "result"
            # message["message"] = result
            # self.send_message(message)

if __name__ == "__main__":
    w = Worker("127.0.0.1", PORT)
