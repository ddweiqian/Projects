from dobot_api import DobotApiFeedBack,DobotApiDashboard
import threading
from time import sleep
import re
import json

class DobotDemo:
    def __init__(self, ip):
        self.ip = ip
        self.dashboardPort = 29999
        self.feedPortFour = 30004
        self.dashboard = None
        self.feedInfo = []
        self.__globalLockValue = threading.Lock()
        self.point_index = 0
        self.point_coordinate_List = []
        
        class item:
            def __init__(self):
                self.robotMode = -1     #
                self.robotCurrentCommandID = 0
                self.MessageSize = -1
                self.DigitalInputs =-1
                self.DigitalOutputs = -1
                self.robotCurrentCommandID = -1
                # 自定义添加所需反馈数据

        self.feedData = item()  # 定义结构对象

    # #original start function
    # def start(self):   
    #     # 启动机器人并使能
    #     self.dashboard = DobotApiDashboard(self.ip, self.dashboardPort)
    #     self.feedFour = DobotApiFeedBack(self.ip, self.feedPortFour)
    #     if self.parseResultId(self.dashboard.EnableRobot())[0] != 0:
    #         print("使能失败: 检查29999端口是否被占用")
    #         return
    #     print("使能成功")

    #     # 启动状态反馈线程
    #     feed_thread = threading.Thread(
    #         target=self.GetFeed)  # 机器状态反馈线程
    #     feed_thread.daemon = True
    #     feed_thread.start()

    #     ## original定义两个目标点
    #     #point_a = [146.3759,-283.4321,332.3956,177.7879,-1.8540,147.5821]
    #     #point_b = [146.3759,-283.4321,432.3956,177.7879,-1.8540,147.5821]

    #     ##20250630 project

    #     #读取工程导出的point.json文件
    #     with open("point_json/point.json", "r", encoding="utf-8") as f :
    #         pointAll = json.load(f) #pointAll现在是所有存点的python列表

    #     #获取所有点位的坐标list
    #     point_coordinate_List= [point["joint"] for point in pointAll]


    #     ## original走点循环
    #     # while True:
    #     #     print("DI:", self.feedData.DigitalInputs,"2DI:", bin(self.feedData.DigitalInputs),"--16:",hex(self.feedData.DigitalInputs))
    #     #     print("DO:", self.feedData.DigitalOutputs,"2DO:" ,bin(self.feedData.DigitalOutputs),"--16:",hex(self.feedData.DigitalOutputs))
    #     #     print("robomode",self.feedData.robotMode)
    #     #     sleep(2)

    #     # 走点循环, #20250630 Project, testing with MOVJ function
    #     while True:
    #         for cor in point_coordinate_List: 
    #             self.RunPoint(cor)
    #             sleep(1)           

    #update original function(start) by spliting into 2 funtions(start and Move) to enable and move to the desinated location
    def start(self): 
        # 启动机器人并使能
        self.dashboard = DobotApiDashboard(self.ip, self.dashboardPort)
        self.feedFour = DobotApiFeedBack(self.ip, self.feedPortFour)
        if self.parseResultId(self.dashboard.EnableRobot())[0] != 0:
            print("使能失败: 检查29999端口是否被占用")
            return
        print("使能成功")

        # 启动状态反馈线程
        feed_thread = threading.Thread(
            target=self.GetFeed)  # 机器状态反馈线程
        feed_thread.daemon = True
        feed_thread.start()

        #读取工程导出的point.json文件
        with open("point_json/point_leftright.json", "r", encoding="utf-8") as f :
            pointAll = json.load(f) #pointAll现在是所有存点的python列表

        #获取所有点位的坐标list
        self.point_coordinate_List= [point["joint"] for point in pointAll]
    
    def Move(self,point_index):
        self.point_index = point_index
        #运动到指定位置
        self.RunPoint(self.point_coordinate_List[self.point_index])
        sleep(1)

    #确认抓夹是否已经release
    def getDO(self):
        try:
            return self.dashboard.GetDO(1)
        except Exception as e:
            print(f"DO_1抓夹状态检测异常: {e}")

    #打开抓夹
    def DORelease(self):
        try:
            self.dashboard.DOInstant(1,1)
            print("打开抓夹DO_1")
        except Exception as e:
            print(f"DO_1抓夹打开异常发生: {e}")

    #关闭抓夹
    def DOClamp(self):
        try:
            self.dashboard.DOInstant(1,0)
            print("关闭抓夹DO_1")
        except Exception as e:
            print(f"DO_1抓夹关闭异常发生: {e}")
    

    def GetFeed(self):
        # 获取机器人状态
        while True:
            feedInfo = self.feedFour.feedBackData()
            with self.__globalLockValue:
                if feedInfo is not None:   
                    if hex((feedInfo['TestValue'][0])) == '0x123456789abcdef':
                        # 基础字段
                        self.feedData.MessageSize = feedInfo['len'][0]
                        self.feedData.robotMode = feedInfo['RobotMode'][0]
                        self.feedData.DigitalInputs = feedInfo['DigitalInputs'][0]
                        self.feedData.DigitalOutputs = feedInfo['DigitalOutputs'][0]
                        self.feedData.robotCurrentCommandID = feedInfo['CurrentCommandId'][0]
                        # 自定义添加所需反馈数据
                        '''
                        self.feedData.DigitalOutputs = int(feedInfo['DigitalOutputs'][0])
                        self.feedData.RobotMode = int(feedInfo['RobotMode'][0])
                        self.feedData.TimeStamp = int(feedInfo['TimeStamp'][0])
                        '''

    def RunPoint(self, point_list):
        # 走点指令
        ##TCP project using MovJ function
        recvmovemess = self.dashboard.MovJ(*point_list, 1)

        # #NewTCP project using MovL function
        # recvmovemess = self.dashboard.MovL(*point_list, 0)
        print("MovJ:", recvmovemess)
        print(self.parseResultId(recvmovemess))
        currentCommandID = self.parseResultId(recvmovemess)[1]
        print("指令 ID:", currentCommandID)
        #sleep(0.02)
        while True:  #完成判断循环

            print(self.feedData.robotMode)
            if self.feedData.robotMode == 5 and self.feedData.robotCurrentCommandID == currentCommandID:
                print("运动结束")
                break
            sleep(0.1)

    def parseResultId(self, valueRecv):
        # 解析返回值，确保机器人在 TCP 控制模式
        if "Not Tcp" in valueRecv:
            print("Control Mode Is Not Tcp")
            return [1]
        return [int(num) for num in re.findall(r'-?\d+', valueRecv)] or [2]

    def __del__(self):
        del self.dashboard
        del self.feedFour
