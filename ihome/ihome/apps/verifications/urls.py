from django.urls import re_path
from . import views

urlpatterns = [
    #
    # # 验证邮箱
    # re_path(r'^emails/verification/$', views.EmailActiveView.as_view()),
    re_path(r'^api/v1.0/imagecode/$',views.ImageCodeView.as_view()),
    re_path(r'^api/v1.0/sms',views.Sms_Code_View.as_view()),
]
