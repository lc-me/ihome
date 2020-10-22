from django.urls import re_path
from . import views

urlpatterns = [
    #
    # # 验证邮箱
    # re_path(r'^emails/verification/$', views.EmailActiveView.as_view()),
    re_path(r'^api/v1.0/users$',views.RegisterView.as_view()),
    re_path(r'^api/v1.0/session$',views.LoginView.as_view()),
    re_path(r'^api/v1.0/user$', views.UserCenterView.as_view()),
    re_path(r'^api/v1.0/user/avatar$',views.AvatarView.as_view()),
    re_path(r'^api/v1.0/user/name$',views.ModifyUserNameView.as_view()),
    re_path(r'^api/v1.0/user/auth$',views.UserAuthView.as_view()),

]
