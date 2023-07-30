import time
import subprocess
import typing
import requests
import json
import suncalc
import sys

from suncalc import getTimes
from datetime import datetime
from random import randint
from math import *
from PyQt5.QtWidgets import QLabel, QGridLayout, QButtonGroup, QRadioButton, QWidget, \
    QSystemTrayIcon, QSizePolicy, QMenu, QAction, qApp, QDesktopWidget
from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSlot, QThread, pyqtSignal, QSize, \
    QPoint, QRectF, QTime
from PyQt5.QtGui import QIcon, QColor, QPainter, QPolygonF

class MainWindow(QWidget):
    """时钟显示在桌面上。通过系统托盘控制"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.getipinfo = {}
        self.getIPinfo()

        self.__lbl1: QLabel = None
        self.__layout: QGridLayout = None
        self.__initUI()

        # 系统托盘
        self.tray_icon = QSystemTrayIcon(self)
        self.__initSystemTray()

        # 默认不启用模拟时钟
        self.isAnalogClock = False

        # 用chatgpt生成的天亮起床提示短语
        self.remind_wakeup = [
        "宝贝，该起床了。",
        "亲爱的，时间不早了。",
        "快起床，我要做早餐了。",
        "起床啦，阳光已经邀请你出门了。",
        "懒虫，起床运动才能让你更有精神。",
        "起来吧，新的一天等着我们。",
        "亲爱的，让我们开始美好的一天吧。",
        "起床了，晚上我会给你一个惊喜的。",
        "起床了，我们可以去吃早餐了。",
        "醒醒，今天是个特别的日子。",
        ]
        # 用chatgpt生成的天黑休息提示短语
        self.remind_sleep = [
        "宝贝，累了一天了，快点闭上眼睛休息吧。",
        "今晚我在你身边，不用担心任何事情，好好休息吧。",
        "我会一直陪在你身边，保护你的梦，让你做个甜美的美梦。",
        "睡前给你一个拥抱，愿你做个安稳的好梦。",
        "明天又是新的一天，听我的话，早点休息。",
        "别想太多了，现在只需要放松就好了。",
        "想到我的温柔，闭上眼睛就可以进入梦乡了。",
        "身体是革命的本钱，好好休息才有更好的明天。",
        "现在该是放下一切，享受美好的睡眠时间的时候了。",
        "晚安，宝贝。我们一起迎接美好的明天。"
        ]
        # 用chatgpt生成的中午吃午饭提示短语
        self.reminder_solarNoon = [
        "我想和你一起分享这顿午餐。",
        "今天的午餐，我希望能和你一起吃。",
        "让我们一起享用这顿美味的午餐吧。",
        "我已经准备好了午饭，你要不要来尝一尝？",
        "吃午饭的时候，有你在身边真是太幸福了。",
        "我为你做了一份特别的午餐，希望你会喜欢。",
        "和你一起吃午饭，是我每天最期待的事情。",
        "你是我最爱的人，和你一起吃午饭是我最快乐的时光。",
        "在这个世界上，没有什么比和你一起吃午饭更美好的事情了。",
        "我的心里只有你，和你一起吃午饭是我最想要的事情。"
        ]
       
        # Timer
        self.__timer = QTimer()
        self.__timer.timeout.connect(self.__timeout)
        self.__timer.start(1000)

    def closeEvent(self, event):
        """重写closeEvent方法拦截窗口关闭事件"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "桌面时钟",
            "桌面时钟已最小化到托盘",
            QSystemTrayIcon.Information,
            2000
        )

    def __initUI(self):

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        """时钟小部件的初始化"""

        localtime = time.localtime()
        str_time = time.strftime("%H:%M:%S", localtime)
        self.__lbl1: QLabel = QLabel(str_time, self)
        self.__lbl1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__lbl1.setAlignment(Qt.AlignCenter)
        self.__lbl1.setStyleSheet("QLabel {color: yellow; font-size:80px;}")

        lbl2str = "%s -> %s -> %s" % (self.getipinfo['country'], self.getipinfo['province'], self.getipinfo['city'])
        self.__lbl2: QLabel = QLabel(lbl2str, self)
        self.__lbl2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__lbl2.setAlignment(Qt.AlignCenter)
        self.__lbl2.setStyleSheet("QLabel {color: yellow; font-size:20px;}")

        lbl3str = "纬度: %s 经度: %s" % (self.getipinfo['longitude'],self.getipinfo['latitude'])
        self.__lbl3: QLabel = QLabel(lbl3str, self)
        self.__lbl3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__lbl3.setAlignment(Qt.AlignCenter)
        self.__lbl3.setStyleSheet("QLabel {color: yellow; font-size:20px;}")

        lbl4str = "运营商: %s -> IP地址: %s" % (self.getipinfo['isp'],self.getipinfo['addr'])
        self.__lbl4: QLabel = QLabel(lbl4str, self)
        self.__lbl4.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__lbl4.setAlignment(Qt.AlignCenter)
        self.__lbl4.setStyleSheet("QLabel {color: yellow; font-size:20px;}")

        self.__layout = QGridLayout()
        self.__layout.addWidget(self.__lbl1, 0, 0)
        self.__layout.addWidget(self.__lbl2, 1, 0)
        self.__layout.addWidget(self.__lbl3, 2, 0)
        self.__layout.addWidget(self.__lbl4, 3, 0)
        self.setLayout(self.__layout)

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint| Qt.WindowStaysOnTopHint)   # hide window and frame
        self.setGeometry(50, 50, 100, 100)
        self.setAttribute(Qt.WA_TranslucentBackground)

        monitor = QDesktopWidget().screenGeometry(1) # monitor secondary monitor
        self.move(monitor.left() + int(monitor.width() / 2 - int(self.width() / 2)), monitor.top())

    def __initSystemTray(self):
        """
        初始化系统托盘部件

            菜单:
            - 显示窗口 - 显示窗口
            - 隐藏窗口 - 隐藏窗口
            - 移动窗口 - 将小部件显示为窗口（可以移动）
            - 固定窗口 - 制作一个没有边框的小部件（不可移动）
            - 数字时钟 - 切换数字/模拟时钟
            - 退出    - 关闭应用程序

        """

        self.tray_icon.setIcon(QIcon("./images/clock.png"))

        # Menu
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)

        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self.hide)

        moveable_action = QAction("移动窗口", self)
        moveable_action.triggered.connect(self.__setMovable)

        immovable_action = QAction("固定窗口", self)
        immovable_action.triggered.connect(self.__setImMovable)

        self.clockSpecies_action = QAction("数字时钟", self)
        self.clockSpecies_action.triggered.connect(self.__clockSpecies)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(moveable_action)
        tray_menu.addAction(immovable_action)
        tray_menu.addAction(self.clockSpecies_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.show()

    def paintEvent(self, event):
        if self.isAnalogClock:
            '''
            实时刷新指针图像
            :param event:
            :return:
            '''
            '''分别定义小时、分钟、秒钟的坐标点'''
            '''
            QPoint(int x, int y);创建坐标点，x、y分别代表横坐标、纵坐标
            '''
            hour_point = [QPoint(7, 8), QPoint(-7, 8), QPoint(0, -30)]
            min_point = [QPoint(7, 8), QPoint(-7, 8), QPoint(0, -65)]
            secn_point = [QPoint(7, 8), QPoint(-7, 8), QPoint(0, -80)]
 
            '''定义三种颜色、用于后面设置三种指针的颜色'''
            hour_color = QColor(182, 98, 0, 182)
            min_color = QColor(0, 130, 130, 155)
            sec_color = QColor(0, 155, 227, 155)
 
            '''获取QWidget对象的宽度和长度的最小值'''
            min_size = min(self.width(), self.height())
 
            painter = QPainter(self)  # 创建坐标系图像绘制对象
            painter.setRenderHint(QPainter.Antialiasing)
 
            # 将QWidget对象的中心位置作为绘制的中心坐标点
            painter.translate(self.width() / 2, self.height() / 2)
 
            # 对尺寸进行缩放
            painter.scale(int(min_size / 200), int(min_size / 200))
 
            # 保存状态
            painter.save()
 
            '''绘制时钟表盘的时间刻度线'''
 
            for a in range(0, 60):
                if (a % 5) != 0:
                    # 每1/60绘制一个刻度线作为分钟刻度线
                    painter.setPen(min_color)
                    painter.drawLine(92, 0, 96, 0)
                else:
                    # 每5/60绘制一个刻度线作为小时刻度线
                    painter.setPen(hour_color)
                    painter.drawLine(88, 0, 96, 0)  # 绘制小时刻度线
                # 每分钟旋转6度
                painter.rotate(360 / 60)
            # 恢复状态
            painter.restore()
 
            '''绘制时钟表盘上面的数字'''
            # 保存状态
            painter.save()
            # 获取字体对象
            font = painter.font()
            # 设置粗体
            font.setBold(True)
            painter.setFont(font)
            # 获取字体大小
            font_size = font.pointSize()
            # 设置之前定义好的颜色
            painter.setPen(hour_color)
            hour_num = 0
            radius = 100
            for i in range(0, 12):
                # 按照12小时制，每三个小时绘制一个小时数字，需要遍历4次
                hour_num = i + 3  # 按QT-Qpainter的坐标系换算，3小时的刻度线对应坐标轴0度
                if hour_num > 12:
                    hour_num = hour_num - 12
                # 根据字体的大小计算出写入小时数字的x、y的位置
                x = radius * 0.8 * cos(i * 30 * pi / 180.0) - font_size
                y = radius * 0.8 * sin(i * 30 * pi / 180.0) - font_size / 2.0
                width = font_size * 2
                height = font_size
                painter.drawText(QRectF(x, y, width, height), Qt.AlignCenter, str(hour_num))
            # 恢复状态
            painter.restore()
 
            '''绘制时钟表盘的时、分、秒的指针'''
 
            # 获取当前时间
            time = QTime.currentTime()
 
            # 绘制小时指针
            painter.save()
            # 取消轮廓线
            painter.setPen(Qt.NoPen)
            # 设置小时指针的颜色
            painter.setBrush(hour_color)
            # 小时指针逆时针旋转
            painter.rotate(30 * (time.hour() + time.minute() / 60))
            # 绘制时钟指针
            painter.drawConvexPolygon(QPolygonF(hour_point))
            # 恢复状态
            painter.restore()
 
            # 绘制分钟指针
            painter.save()
            # 取消轮廓线
            painter.setPen(Qt.NoPen)
            # 设置分钟指针的颜色
            painter.setBrush(min_color)
            # 分钟指针逆时针旋转
            painter.rotate(6 * (time.minute() + time.second() / 60))
            # 绘制分钟指针
            painter.drawConvexPolygon(QPolygonF(min_point))
            # 恢复状态
            painter.restore()
 
            # 绘制秒钟指针
            painter.save()
            # 取消轮廓线
            painter.setPen(Qt.NoPen)
            # 设置秒针颜色
            painter.setBrush(sec_color)
            # 秒钟指针逆时针旋转
            painter.rotate(6 * time.second())
            # 绘制秒钟指针
            painter.rotate(0.5)
            painter.drawConvexPolygon(QPolygonF(secn_point))
            # 恢复状态
            painter.restore()

    @pyqtSlot()
    def __clockSpecies(self):
        if self.isAnalogClock:
            self.clockSpecies_action.setText('数字时钟')
            self.isAnalogClock = False
            self.__lbl1.show()
            self.__lbl2.show()
            self.__lbl3.show()
            self.__lbl4.show()
        else:
            self.clockSpecies_action.setText('模拟时钟')
            self.isAnalogClock = True
            self.__lbl1.hide()
            self.__lbl2.hide()
            self.__lbl3.hide()
            self.__lbl4.hide()

    @pyqtSlot()
    def __timeout(self):
        localtime = time.localtime()
        # 日期默认输出格式2021-06-25,把06前面的0去掉只需在格式化%后面加上#就可以了,%-适用于Linux平台,%#适用于Windows平台.
        hour = time.strftime("%-H", localtime)
        minute = time.strftime("%M", localtime)
        second = time.strftime("%S", localtime)
        sTime = time.strftime("%H:%M:%S", localtime)
        self.__lbl1.setText(str(sTime))
        # 整点、半点报时
        if minute == "00":
            if second == "00":
                print(sTime)
                self.speak("主人！已经%s点了" % (hour))
        elif minute == "30":
            if second == "00":
                print(sTime)
                self.speak("主人！已经%s点%s分了" % (hour,minute))
        # 使用太阳/月亮位置计算器计算天文时间并提醒， 比如中午、深夜
        if self.isSuncalcTime(localtime, 'solarNoon'):
            # 中午提醒
            self.speak(self.reminder_solarNoon[randint(0,9)])
        elif self.isSuncalcTime(localtime, 'nadir'):
            # 深夜提醒
            self.speak(self.remind_sleep[randint(0,9)])
        elif self.isSuncalcTime(localtime, 'sunriseEnd'):
            # 天亮提醒
            self.speak(self.remind_wakeup[randint(0,9)])
        elif self.isSuncalcTime(localtime, 'sunset'):
            # 天黑提醒
            self.speak("当前天文时刻：日落结束，黑夜即将开始！")
        # 模拟时钟需要update否则秒针不走
        self.update()
        # print("SayTime 执行中...")
        
    @pyqtSlot()
    def __setMovable(self):
        """非固定模式"""
        self.setWindowFlags(Qt.Tool)
        self.show()

    @pyqtSlot()
    def __setImMovable(self):
        """固定模式"""
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def speak(self, text):
        subprocess.Popen(['edge-playback', '--voice', 'zh-CN-XiaoxiaoNeural', '--text', text], shell=False)

    def isSuncalcTime(self, LocalTime, SuncalcTimeStr):
        # 计算是否是天文时间
        SuncalcTime = getTimes(datetime.now(), float(int(float(self.getipinfo['latitude']))), float(int(float(self.getipinfo['longitude']))))
        '''
            SuncalcTime['solarNoon'] 中午时间
            SuncalcTime['nadir'] 深夜时间
            SuncalcTime['sunrise'] 日出时间 太阳即将出现在地平线
            SuncalcTime['sunset'] 日落时间 太阳完全消失在地平线
            SuncalcTime['sunriseEnd'] 日出结束时间 太阳完全出现在地平线
            SuncalcTime['sunsetStart'] 日落开始时间 太阳即将消失在地平线
            SuncalcTime['dawn'] 黎明时间
            SuncalcTime['dusk'] 黄昏时间
            SuncalcTime['nauticalDawn'] 海上黎明时间
            SuncalcTime['nauticalDusk'] 海上黄昏时间
            SuncalcTime['nightEnd'] 黑夜结束时间 - 月亮消失时间
            SuncalcTime['night'] 黑夜时间 - 月亮出现时间
            SuncalcTime['goldenHourEnd'] 天文曙暮光结束时间
            SuncalcTime['goldenHour'] 天文曙暮光时间
        '''
        # print(SuncalcTime)
        dt = datetime.strptime(SuncalcTime[SuncalcTimeStr],'%Y-%m-%d %H:%M:%S')
        print(dt)
        ds = dt.strftime("%H:%M:%S")
        # print(ds)
        if time.strftime("%H:%M:%S", LocalTime) == datetime.strptime(SuncalcTime[SuncalcTimeStr],'%Y-%m-%d %H:%M:%S').strftime("%H:%M:%S"):
            return True
        return False
    
    def getIPinfo(self):
        # 使用bilibili的api查询ip和物理地址信息
        '''
        self.getipinfo['addr'] IP地址
        self.getipinfo['country'] 国家
        self.getipinfo['province'] 省份
        self.getipinfo['city'] 城市
        self.getipinfo['isp'] 运营商
        self.getipinfo['longitude'] 经度
        self.getipinfo['latitude'] 纬度
        '''
        res = requests.get("https://api.live.bilibili.com/xlive/web-room/v1/index/getIpInfo")
        ipinfo_res = json.loads(res.text)
        ipinfo = ipinfo_res['data']
        self.getipinfo['addr'] = ipinfo['addr']
        self.getipinfo['country'] = ipinfo['country']
        self.getipinfo['province'] = ipinfo['province']
        self.getipinfo['city'] = ipinfo['city']
        self.getipinfo['isp'] = ipinfo['isp']
        self.getipinfo['latitude'] = ipinfo['latitude']
        self.getipinfo['longitude'] = ipinfo['longitude']
        # print(res.text)
        # print(ipinfo['addr'])

