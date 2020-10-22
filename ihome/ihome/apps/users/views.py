import json
import logging
import re

from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection

from django.conf import settings
from ihome.libs.qiniuyun.qiniu_storage import storage
from ihome.utils.parameter_checking import image_file
from users.models import User

logger = logging.getLogger('django')


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
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile,
                                            avatar=None)
        except Exception as e:
            return JsonResponse({
                'errno': '4004',
                'ermsg': '用户创建失败'
            })
        login(request, user)

        return JsonResponse({
            'errno': '0',
            'errmsg': 'OK'
        })


class LoginView(View):
    def post(self, request):
        json_data = json.loads(request.body.decode())
        mobile = json_data.get('mobile')
        password = json_data.get('password')

        if not all([password, mobile]):
            return JsonResponse({
                'errno': '4004',
                'errmsg': '缺少必传参数'
            })
        user = authenticate(username=mobile,
                            password=password)

        if not user:
            return JsonResponse({
                'errno': '4002',
                'errmsg': '用户不存在'
            })
        login(request, user)

        request.session.set_expiry(60 * 60 * 24 * 7)

        response = JsonResponse({
            'errno': '0',
            'errmsg': 'OK'
        })

        response.set_cookie('username', user.username, max_age=3600 * 24 * 7)
        return response

    def get(self, request):
        username = request.COOKIES.get('username')
        username2 = request.session.get('username')
        if not username:
            return JsonResponse({
                'errno': '4101',
                'errmsg': '未登录'
            })
        return JsonResponse({
            'errno': '0',
            'errmsg': '已登录',
            'data': {
                'name': username
            }
        })

    def delete(self, request):
        logout(request)

        response = JsonResponse({
            'errno': '0',
            'errmsg': '以登出'
        })
        response.delete_cookie('username')

        return response


class UserCenterView(View):
    def get(self, request):
        user = request.user
        data_dict = {
            'avatar': 'http://oyucyko3w.bkt.clouddn.com/' + str(user.avatar),
            'create_time': user.date_joined,
            'mobile': user.mobile,
            'name': user.username,
            'user_id': user.id
        }
        return JsonResponse({
            'data': data_dict,
            'errno': '0',
            'errnsg': 'ok'
        })
        # return JsonResponse({'errno':'0','errmsg':'OK','data':user.to_basic_dict()})


class AvatarView(View):
    def post(self, request):
        avatar = request.FILES.get('avatar')
        if not avatar:
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})

        if not image_file(avatar):
            return JsonResponse({'errno': '4103', 'errmsg': '参数错误'})

        file_data = avatar.read()

        try:
            key = storage(file_data)

        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': '400', 'errmsg': '上传图片失败'})

        try:
            request.user.avatar = key
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': '400', 'errmsg': '图片保存失败'})

        data = {
            'avatar_url': settings.QINIU_URL + key
        }

        return JsonResponse({'error': '0', 'errmsg': '修改成功'})


class ModifyUserNameView(View):
    def put(self, request):
        json_data = json.loads(request.body.decode())

        new_name = json_data.get('name')

        try:
            request.user.username = new_name
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': '4500', 'errmsg': '修改名字失败'})
        return JsonResponse({'errno': '0', 'errmsg': '修改用户名成功'})


class UserAuthView(View):
    def post(self, request):
        json_data = json.loads(request.body.decode())
        real_name = json_data.get('real_name')
        id_card = json_data.get('id_card')
        if not all([real_name, id_card]):
            return JsonResponse({'errno': '4004', 'errmsg': '缺少参数'})
        try:
            request.user.id_card = id_card
            request.user.real_name = real_name
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'errno': '4500', 'errmsg': '数据保存失败'})

        return JsonResponse({'errno': '0', 'errmsg': 'ok'})

    def get(self, request):
        data = {
            'real_name': request.user.real_name,
            'id_card': request.user.id_card
        }
        return JsonResponse({'errno':'0','errmsg':'OK','data':data})
