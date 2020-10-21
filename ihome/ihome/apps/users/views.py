import json
import re

from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from users.models import User


class RegisterView(View):
    def post(self, request):
        json_data = json.loads(request.body.decode())
        mobile = json_data.get('mobile')
        password = json_data.get('password')
        sms_code_client = json_data.get('phonecode')
        if not all([mobile, password, sms_code_client]):
            return JsonResponse({
                'errno': '4103',
                'errmsg': '缺少必传参数'
            })
        if not re.match(r'^[0-9a-zA-Z]{6,20}$', password):
            return JsonResponse({
                'errno': '4004',
                'errmsg': '密码格式错误，请输入6-20位密码'
            })
        redis_conn = get_redis_connection('verify_code')

        sms_code_server = redis_conn.get('sms_%s' % mobile).decode()

        if not sms_code_server:
            return JsonResponse({'code': 400,
                                 'errmsg': '短信验证码过期'})
        if sms_code_client != sms_code_server:
            return JsonResponse({
                'errno': '4004',
                'errmsg': '短信验证码不一致'
            })

        try:
            user=User.objects.create_user(username=mobile,
                                          password=password,
                                          mobile=mobile)
        except Exception as e:
            return JsonResponse({
                'errno':'4004',
                'ermsg':'用户创建失败'
            })
        login(request,user)

        return JsonResponse({
            'errno':'0',
            'errmsg':'OK'
        })
