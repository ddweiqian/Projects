import socket
from time import sleep
import os
import configparser
from DobotDemo import DobotDemo
import json



class Dobot_server():
    """初始化机械臂"""
    def __init__(self, ip="127.0.0.1", port=1111, config_path="config/server.ini"):
        self.config = self._load_config(config_path)

        self.ip = ip
        self.port = port
        self.socket_dobot = 0
        self.conn = None

        self.cmdHandshake = self.config.get('COMMANDS', 'handshake')
        self.RespHandshake = self.config.get('RESPONSE', 'handshake')

        self.cmdStartup = self.config.get('COMMANDS', 'startup')
        self.RespStartup = self.config.get('RESPONSE', 'startup')

        self.cmdRelease = self.config.get('COMMANDS', 'RELEASE')
        self.RespRelease = self.config.get('RESPONSE', 'RELEASE')

        self.cmdClamping= self.config.get('COMMANDS', 'clamping')
        self.RespClamping= self.config.get('RESPONSE', 'clamping')

        self.cmdMove2next = self.config.get('COMMANDS', 'move2next')
        self.RespMove2next = self.config.get('RESPONSE', 'move2next')

        self.cmdClear_error = self.config.get('COMMANDS', 'clear_error')
        self.RespClear_error = self.config.get('RESPONSE', 'clear_error')

        self.RespFinished = self.config.get('RESPONSE', 'finished')
        self.RespError = self.config.get('RESPONSE', 'ERROR')

        self.current_index = 0  # track current point
        self.last_index = 0 #verify the last point
        self.Dostatus = 0 # 抓夹打开/关闭状态（0为关闭(抓紧），1为打开）
         #读取工程导出的point.json文件
        with open("point_json/point_leftright.json", "r", encoding="utf-8") as f :
            pointAll = json.load(f) #pointAll现在是所有存点的python列表

        #获取所有点位的坐标list
        self.point_coordinate_List= [point["joint"] for point in pointAll]
        
        print("初始化机械臂server完成!")
          
        if self.port == 1111:
            try:
                self.socket_dobot =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_dobot.bind((self.ip, self.port))  # Bind to port 1111
                self.socket_dobot.listen()           # dobot Start listening for client
                print(f"机械臂启动，监听端口 {self.port}...")
                self.conn, addr = self.socket_dobot.accept() #self.conn is a connected client socket
                print(f"机械臂连接到端口{self.port}...")

            except socket.error as e:
                if e.errno == 98:  # Address already in use
                    print(f"{self.RespError}连接机械臂失败，端口 {self.port} 被占用!")
                else:
                    print(f"{self.RespError}Socket错误 : {e}") 
        else:
            print(f"{self.RespError}连接到机械臂需要端口 {self.port} !")      


    def _load_config(self, config_path):
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"{self.RespError}配置文件不存在: {config_path}")       
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        return config
    
    def send_Reply(self, string):
        """Send a reply for a command."""
        print(f"发送回复给 {self.ip}:{self.port}: {string}")
        try:
            self.conn.send(str.encode(string, 'utf-8'))
        except Exception as e:
            print(f"{self.RespError}回复主程序失败 {e}, 尝试重连接...")
            while True:
                try:
                    self.conn = self.reConnect()
                    print(f"重连接完成 ！")
                    self.conn.send(str.encode(string, 'utf-8'))
                    print(f"回复主程序完成 ！")
                    break
                except Exception as e:
                    print(f"{self.RespError}重连接失败{e} ！")
                    sleep(1) 


    def reConnect(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.socket_dobot:
                    self.socket_dobot.bind((self.ip, self.port))  # Bind to port 1111
                    self.socket_dobot.listen()           # dobot Start listening for client
                    print("[INFO] 端口监听中...，等待客户端重连...")
                    self.conn, addr = self.socket_dobot.accept()
                    print(f"[INFO] 重连接 {addr}")
                    break
            except Exception as e:
                print(f"{self.RespError}重连接错误 : {e}") 
                sleep(1)
        return self.conn
    
    def wait_cmd(self):
        """
        Read the return value
        """
        data = ""
        try:
            if self.conn is None:
                print(f"{self.RespError} No client connected. Waiting for client...")
                self.conn = self.reConnect()
            data = self.conn.recv(1024)
        except Exception as e:
            print(f"{self.RespError} Receiving data failed: {e}")
            self.socket_dobot = self.reConnect()

        finally:
            if len(data) == 0:
                data_str = data
            else: 
                data_str = str(data, encoding="utf-8")
            print(f'收到来自 {self.ip}:{self.port}: {data_str}')
            return data_str    
    
    def close(self):
        """
        Close the port
        """
        if (self.socket_dobot!= 0):
            try:
                self.socket_dobot.shutdown(socket.SHUT_RDWR)
                self.socket_dobot.close()
            except socket.error as e:
                print(f"{self.RespError}Error while closing socket: {e}")
        
    def __del__(self):
        self.close()


    def serverStart(self):
        try:
            while True:
              data = self.wait_cmd()
              if not data:
                  continue
              response = self.process_command(data)
              if response is not None:
                if response == self.RespStartup :
                    dobot.Move(self.current_index) # move to initial position to startup or loop reset
                    self.Dostatus= dobot.getDO() #检查机械臂是否已经打开（0为关闭，1为打开）
                    if  self.Dostatus == 0 :
                        dobot.DORelease()
                elif response == self.RespHandshake :
                    dobot.start()
                elif response == self.RespRelease:
                    dobot.DORelease()
                elif response == self.RespClamping:
                    dobot.Move(self.current_index+1) #假设clamping点位的序号，是初始点位序号+1
                    dobot.DOClamp()
                self.send_Reply(response)
        except Exception as e:
            print(f"{self.RespError}机械臂异常发生: {e}")
        finally:
            if self.socket_dobot:
                self.socket_dobot.close()
    
    def move_to_next(self):
        #test
        print(f"[DEBUG] move_to_next triggered.")

        try:
            # Start from current point (typically in every loop it is 1)
            if self.current_index < len(self.point_coordinate_List)-1:
                print(f"Moving to next point in the loop...")
                #next_point = self.point_coordinate_List[self.current_index]
                next_point = self.current_index + 1
                dobot.Move(next_point)
                self.send_Reply(self.RespMove2next)
                self.current_index = next_point 
            elif self.current_index == len(self.point_coordinate_List)-1:
                # After reaching the end, reply "finished" to client to inform the last point of loop
                print(f"Moving to the last point of the loop")
                self.last_index = self.current_index  # label last point for relase
                dobot.Move(self.last_index)
                self.send_Reply(self.RespFinished)
                self.current_index = 0  
                self.last_index  = 0              
        except Exception as e:
            print(f"{self.RespError}Error during move_to_next loop: {e}")


    def process_command(self, command):
        if command == self.cmdHandshake:
            return self.RespHandshake
        elif command == self.cmdStartup:
            return self.RespStartup
        elif command == self.cmdRelease :
            return self.RespRelease
        elif command == self.cmdClamping:
            return self.RespClamping
        elif command == self.cmdMove2next:
            self.move_to_next()
        elif command == self.cmdClear_error:
            return self.RespClear_error
        else:
            return "REPLY=UNKNOWN COMMAND!"
            
        
if __name__ == "__main__":
    try:
        dobot = DobotDemo("192.168.2.100")
        print("初始化机械臂完成!")
        server = Dobot_server()
        server.serverStart()
    except KeyboardInterrupt:
        print("检测到键盘中断，正在停止...")
        if hasattr(server, 'stop'):
            server.stop()
    except Exception as e:
        print(f"运行异常: {str(e)}")
        import traceback
        traceback.print_exc()