#-*- codeing = utf-8 -*-
#@Author: lc
#@Software: PyCharm
#@File: parameter_checking.py
#@Time: 2020/10/21 下午7:25

import imghdr


def image_file(value):
    '''
    检查是否是图片文件
    防止上传其他文件
    :param value:
    :return:
    '''
    try:
        file_type=imghdr.what(value)
        return file_type if file_type else None
    except:
        return None