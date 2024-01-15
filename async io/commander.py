from client import Client
import time
from constants import PORT
import base64
import os

class Commander(Client):
    def __init__(self, IP, port):
        super().__init__(IP, port)
        self.type = "commander"
        self.socket.connect((self.IP, self.port))
        self.send_message(self.type)
        self.send_message(self.ID)
        print(f"[INFO] Client {self.ID} connected to server")
        self.start_message_loop()
                

    def start_message_loop(self):
        while True:
            user_input = input("Press Enter to send the function (or type 'exit' to quit): ")
            
            # read file
            f = open("./cube_diorama/jiggly_pudding.blend", "rb")
            file = f.read()

            start = time.time()

            start_frame = 1
            end_frame = 120
            
            message = {
                # "file": file,
                "file_name": "jiggly_pudding.blend",
                "file": base64.b64encode(file).decode('utf-8'),
                "start_frame": start_frame,
                "end_frame": end_frame,
                }
            # send file
            self.send_message(message)
            print(f"[INFO] File sent to server")


            output_folder = "commander_output"
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            
            # length = self.receive_message()
            no_of_frames = end_frame - start_frame + 1
            for i in range(no_of_frames):
                message = self.receive_message()
                if message is None:
                    break
                frame_num = message["frame_num"]
                f = open(f"{output_folder}/{frame_num}.png", "wb")
                f.write(base64.b64decode(message["frame"]))
                f.close()
                print(f"[INFO] Received result for frame {frame_num}", end="\r")

                
           
            # message = ""
            # for i in range(len(result)):
            #     message += result[i]["message"]+" "
            #     # message += result[i]["message"]
            # print(f"[INFO] Result received from server: {message}")
            # end = time.time()
            # print(end - start)
   
            end = time.time()
            print(f"[INFO] Rendered {end_frame} frames in {end - start} seconds")
                

c = Commander("192.168.0.107", PORT)

