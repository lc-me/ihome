import json
import logging
import re

logger = logging.getLogger('django')
import random
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from ihome.libs.captcha.captcha import captcha


class ImageCodeView(View):
    def get(self, request):
        cur = request.GET.get('cur')
        pur = request.GET.get('pur')
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % cur, 300, text)
        return HttpResponse(image,
                            content_type='image/jpg')


class Sms_Code_View(View):
    def post(self, request):
        redis_conn = get_redis_connection('verify_code')
        flag=redis_conn.get('flag')
        if flag is not None:
            return JsonResponse({
                'errno':'400',
                'errmsg':'频繁请求发送短信，请1分钟后重试'
            })

        json_data = json.loads(request.body.decode())
        mobile = json_data['mobile']
        id = json_data['id']
        text = json_data['text']
        if not all([mobile, id, text]):
            return JsonResponse({
                'errno': '400',
                'errmsg': '缺少必传参数'
            })
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return JsonResponse({
                'errno':'4004',
                'errmsg':'电话号码有误'
            })

        #从数据库里取出来的是byte类型
        img_code_server = redis_conn.get('img_%s' % id)
        img_code_server = img_code_server.decode()

        if img_code_server is None:
            return JsonResponse({
                'errno': '400',
                'errmsg': '验证码过期'
            })
        # 取完就把redis里面验证码删除，保证验证码只能用一次
        try:
            redis_conn.delete('img%s' % id)
        except Exception as e:
            logger.error(e)

        if text.lower() != img_code_server.lower():
            return JsonResponse({
                'errno':'400',
                'errmsg':"验证码错误"
            })
        sms_code='%06d'%random.randint(0,999999)
        logger.info(sms_code)

        redis_conn.setex(
            'sms_%s'%mobile,
            300,
            sms_code
        )
        redis_conn.setex(
            'flag',
            60,
            1
        )
        return JsonResponse({
            'errno':'0',
            'errmsg':'发送成功'
        })