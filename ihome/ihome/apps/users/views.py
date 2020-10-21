import json
import re

from django.contrib.auth import login, authenticate, logout
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

class LoginView(View):
    def post(self,request):
        json_data=json.loads(request.body.decode())
        mobile=json_data.get('mobile')
        password=json_data.get('password')

        if not all([password,mobile]):
            return JsonResponse({
                'errno':'4004',
                'errmsg':'缺少必传参数'
            })
        user=authenticate(username=mobile,
                          password=password)

        if not user:
            return JsonResponse({
                'errno':'4002',
                'errmsg':'用户不存在'
            })
        login(request,user)

        request.session.set_expiry(60*60*24*7)

        response = JsonResponse({
            'errno':'0',
            'errmsg':'OK'
        })

        response.set_cookie('username',user.username,max_age=3600*24*7)
        return response
    def get(self,request):
        username=request.COOKIES.get('username')
        username2 = request.session.get('username')
        if not username:
            return JsonResponse({
                'errno':'4101',
                'errmsg':'未登录'
            })
        return JsonResponse({
            'errno':'0',
            'errmsg':'已登录',
            'data':{
                'name':username
            }
        })

    def delete(self,request):
        logout(request)

        response=JsonResponse({
            'errno':'0',
            'errmsg':'以登出'
        })
        response.delete_cookie('username')

        return response