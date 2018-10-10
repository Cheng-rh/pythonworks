# -!- coding: utf-8 -!-
# !/usr/bin/python
# Created with pycharm.
# File Name: VideoToChar 
# User: bolao
# Date: 2018/9/21 15:16
# Version: V1.0
# To change this template use File | Settings | File Templates.
# Description:   主要是利用python将短视频转换为字符串的视频

import sys
import os
import time
import threading
import cv2
import pyprind
import argparse


class CharFrame:
    # 主要是用来映射图片对应的字符串
    ascii_char = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

    # 像素映射到字符（每个灰度值对应其中的一个字符串）
    def pixelToChar(self, luminance):
        return self.ascii_char[int(luminance / 256 * len(self.ascii_char))]

    # 将普通帧转为 ASCII 字符帧
    def convert(self, img, limitSize=-1, fill=False, wrap=False):
        if limitSize != -1 and (img.shape[0] > limitSize[1] or img.shape[1] > limitSize[0]):
            # 重新设置图片的大小，其中interpolation=cv2.INTER_AREA 表示的是图片的插值方法
            img = cv2.resize(img, limitSize, interpolation=cv2.INTER_AREA)
        # 如果宽度不够的话就用“ ”来填充，如果高度不够的话，就用“\n”来填充。
        blank = ''
        if fill:
            blank += ' ' * (limitSize[0] - img.shape[1])
        if wrap:
            blank += '\n'
        # 获取图片的每个灰度值并将其转换为字符串，ascii_frame 表示初始化每行的字符串
        ascii_frame = ''
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                ascii_frame += self.pixelToChar(img[i, j])
            ascii_frame += blank
        return ascii_frame


class I2Char(CharFrame):
    result = None

    def __init__(self, path, limitSize=-1, fill=False, wrap=False):
        self.genCharImage(path, limitSize, fill, wrap)

    def genCharImage(self, path, limitSize=-1, fill=False, wrap=False):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return
        self.result = self.convert(img, limitSize, fill, wrap)

    def show(self, stream=2):
        if self.result is None:
            return
        if stream == 1 and os.isatty(sys.stdout.fileno()):
            self.streamOut = sys.stdout.write
            self.streamFlush = sys.stdout.flush
        elif stream == 2 and os.isatty(sys.stderr.fileno()):
            self.streamOut = sys.stderr.write
            self.streamFlush = sys.stderr.flush
        elif hasattr(stream, 'write'):
            self.streamOut = stream.write
            self.streamFlush = stream.flush
        self.streamOut(self.result)
        self.streamFlush()
        self.streamOut('\n')


class V2Char(CharFrame):
    charVideo = []
    # 表示的是时间间隔
    timeInterval = 0.033

    def __init__(self, path):
        '''
        构造器初始化
        :param path: 待转换字符串的视频地址
        '''
        # 根据文件的后缀，打开对应的文件
        if path.endswith('txt'):
            self.load(path)
        else:
            self.genCharVideo(path)

    def genCharVideo(self, filepath):
        '''
        用来获取对应的字符video
        :param filepath: 待转换字符串的视频地址
        :return:
        '''
        self.charVideo = []
        cap = cv2.VideoCapture(filepath)
        # cap.get(5) 获取的是视频原本的fps, 通过fps获取视频的间隔，其中round(1 / cap.get(5), 3)的方法表示的是四舍五入的值：round(80.23456, 2) :  80.23
        self.timeInterval = round(1 / cap.get(5), 3)
        # cap.get(7) 表示获取视频的总帧数
        nf = int(cap.get(7))
        print('Generate char video, please wait...')
        # 其中 pyprind.prog_bar 是python中的非常实用的进度条小工具
        for i in pyprind.prog_bar(range(nf)):
            # cv2.cvtColor是opencv的颜色空间转换
            # cap.read() 返回值的第一个参数为true 或者false，表示的是有没有读取到图片。第二个参数framme，表示截取到一帧的图片
            # cv2.COLOR_BGR2GRAY是转换类型 BGR和灰度图的转换使用
            rawFrame = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY)
            # os.get_terminal_size()表示获取终端的宽度，根据不同的终端自适应的打出一行。返回的是转换成字符串的每张照片(字符)
            frame = self.convert(rawFrame, os.get_terminal_size(), fill=True)
            self.charVideo.append(frame)
        cap.release()

    def export(self, filepath):
        if not self.charVideo:
            return
        with open(filepath, 'w') as f:
            for frame in self.charVideo:
                # 加一个换行符用以分隔每一帧
                f.write(frame + '\n')

    def load(self, filepath):
        self.charVideo = []
        # 一行即为一帧
        for i in open(filepath):
            self.charVideo.append(i[:-1])

    def play(self, stream=1):
        # Bug:
        # 光标定位转义编码不兼容 Windows
        if not self.charVideo:
            return
        if stream == 1 and os.isatty(sys.stdout.fileno()):
            self.streamOut = sys.stdout.write
            self.streamFlush = sys.stdout.flush
        elif stream == 2 and os.isatty(sys.stderr.fileno()):
            self.streamOut = sys.stderr.write
            self.streamFlush = sys.stderr.flush
        elif hasattr(stream, 'write'):
            self.streamOut = stream.write
            self.streamFlush = stream.flush
        breakflag = False

        def getChar():
            nonlocal breakflag
            try:
                # 若系统为 windows 则直接调用 msvcrt.getch()
                import msvcrt
            except ImportError:
                import termios, tty
                # 获得标准输入的文件描述符
                fd = sys.stdin.fileno()
                # 保存标准输入的属性
                old_settings = termios.tcgetattr(fd)
                try:
                    # 设置标准输入为原始模式
                    tty.setraw(sys.stdin.fileno())
                    # 读取一个字符
                    ch = sys.stdin.read(1)
                finally:
                    # 恢复标准输入为原来的属性
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                if ch:
                    breakflag = True
            else:
                if msvcrt.getch():
                    breakflag = True

        # 创建线程
        getchar = threading.Thread(target=getChar)
        # 设置为守护线程
        getchar.daemon = True
        # 启动守护线程
        getchar.start()
        # 输出的字符画行数
        rows = len(self.charVideo[0]) // os.get_terminal_size()[0]
        for frame in self.charVideo:
            # 接收到输入则退出循环
            if breakflag:
                break
            self.streamOut(frame)
            self.streamFlush()
            time.sleep(self.timeInterval)
            # 共 rows 行，光标上移 rows-1 行回到开始处
            self.streamOut('\033[{}A\r'.format(rows - 1))
        # 光标下移 rows-1 行到最后一行，清空最后一行
        self.streamOut('\033[{}B\033[K'.format(rows - 1))
        # 清空最后一帧的所有行（从倒数第二行起）
        for i in range(rows - 1):
            # 光标上移一行
            self.streamOut('\033[1A')
            # 清空光标所在行
            self.streamOut('\r\033[K')
        if breakflag:
            self.streamOut('User interrupt!\n')
        else:
            self.streamOut('Finished!\n')


if __name__ == '__main__':

    # # 其中argparse是一个命令解析器，设置命令行参数(python **.py ... -e ...)
    # parser = argparse.ArgumentParser()
    # parser.add_argument('file', help='Video file or charvideo file')
    # parser.add_argument('-e', '--export', nargs='?', const='charvideo.txt', help='Export charvideo file')
    # # 获取参数
    # args = parser.parse_args()

    videoPath = r"C:\Users\sssd\Desktop\Apple.mp4"
    savePath = r"G:\result.txt"
    # 读取视频video并转换为char.
    v2char = V2Char(videoPath)
    v2char.export(savePath)
    v2char.play()
