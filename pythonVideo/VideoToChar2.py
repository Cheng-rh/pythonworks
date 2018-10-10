# -!- coding: utf-8 -!-
# !/usr/bin/python
# Created with pycharm.
# File Name: VideoToChar 
# User: bolao
# Date: 2018/9/27 11:18
# Version: V1.0
# To change this template use File | Settings | File Templates.
# Description:

import argparse
import os
import cv2
import subprocess
from cv2 import VideoWriter, VideoWriter_fourcc, imread, resize
from PIL import Image, ImageFont, ImageDraw

# 命令行输入参数处理
# parser = argparse.ArgumentParser()
# parser.add_argument('file')
# parser.add_argument('-o', '--output')
# parser.add_argument('-f', '--fps', type=float, default=24)  # 帧
# parser.add_argument('-s', '--save', type=bool, nargs='?', default=False, const=True)

#  获取参数
# args = parser.parse_args()
# INPUT = args.file
# OUTPUT = args.output
# SAVE = args.save
# FPS = args.fps

# 像素对应的ascii码
ascii_char = list(".@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'$ ")


def video2txt_jpg(fileName):
    '''
    加载视频，获取每一帧图像
    :param fileName:
    :return:
    '''
    vc = cv2.VideoCapture(fileName)
    c = 1
    if vc.isOpened():
        r, frame = vc.read()
        if not os.path.exists('Cache'):
            os.mkdir('Cache')
        # 用于改变当前工作目录到指定的路径
        os.chdir('Cache')
    else:
        r = False
    while r:
        cv2.imwrite(str(c) + '.jpg', frame)
        txt2image(str(c) + '.jpg')  # 同时转换为ascii图
        r, frame = vc.read()
        c += 1
    os.chdir('..')
    return vc


def txt2image(fileName):
    '''
    获取视频每一帧的图像，并转换成对应的字符串
    :param fileName:
    :return:
    '''
    im = Image.open(fileName).convert('RGB')
    raw_width = im.width
    raw_height = im.height
    width = int(raw_width / 6)
    height = int(raw_height / 15)
    im = im.resize((width, height), Image.NEAREST)

    txt = ""
    colors = []
    for i in range(height):
        for j in range(width):
            # 返回给定位置的像素值
            pixel = im.getpixel((j, i))
            colors.append((pixel[0], pixel[1], pixel[2]))
            if (len(pixel) == 4):
                txt += get_char(pixel[0], pixel[1], pixel[2], pixel[3])
            else:
                txt += get_char(pixel[0], pixel[1], pixel[2])
        txt += "\n"
        colors.append((255, 255, 255))

    im_txt = Image.new("RGB", (raw_width, raw_height), (255, 255, 255))
    dr = ImageDraw.Draw(im_txt)
    font = ImageFont.load_default()
    x = y = 0
    # 获取字体的宽高
    font_w, font_h = font.getsize(txt[1])
    font_h *= 1.37
    # ImageDraw为每个ascii码进行上色
    for i in range(len(txt)):
        if (txt[i] == '\n'):
            x += font_h
            y = -font_w
        dr.text((y, x), txt[i], colors[i], font)
        y += font_w
    name = fileName
    print(name + ' changed')
    im_txt.save(name)


def get_char(r, g, b, alpha=256):
    '''
    主要是获取每个像素对应的数值
    :param r:
    :param g:
    :param b:
    :param alpha:
    :return:
    '''
    if alpha == 0:
        return ''
    length = len(ascii_char)
    gray = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
    unit = (256.0 + 1) / length
    return ascii_char[int(gray / unit)]


def jpg2video(outfile_name, fps):
    fourcc = VideoWriter_fourcc(*"MJPG")
    images = os.listdir('Cache')
    im = Image.open('Cache/' + images[0])
    vw = cv2.VideoWriter(outfile_name + '.avi', fourcc, fps, im.size)
    os.chdir('Cache')
    for image in range(len(images)):
        # Image.open(str(image)+'.jpg').convert("RGB").save(str(image)+'.jpg')
        frame = cv2.imread(str(image + 1) + '.jpg')
        vw.write(frame)
        print(str(image + 1) + '.jpg' + ' finished')
    os.chdir('..')
    vw.release()


def video2mp3(file_name):
    '''
    调用ffmpeg获取mp3音频文件
    :param file_name:
    :return:
    '''
    outfile_name = file_name.split('.')[0] + '.mp3'
    subprocess.call('ffmpeg -i ' + file_name + ' -f mp3 ' + outfile_name, shell=True)


def video_add_mp3(file_name, mp3_file):
    outfile_name = file_name.split('.')[0] + '-txt.mp4'
    subprocess.call('ffmpeg -i ' + file_name + ' -i ' + mp3_file + ' -strict -2 -f mp4 ' + outfile_name, shell=True)


if __name__ == '__main__':
    INPUT = r'C:\Users\sssd\Desktop\Apple.mp4'
    vc = video2txt_jpg(INPUT)
    FPS = vc.get(cv2.CAP_PROP_FPS)  # 获取帧率
    vc.release()
    jpg2video(INPUT.split('.')[0], FPS)
    print(INPUT, INPUT.split('.')[0] + '.mp3')
    video2mp3(INPUT)
    video_add_mp3(INPUT.split('.')[0] + '.avi', INPUT.split('.')[0] + '.mp3')
