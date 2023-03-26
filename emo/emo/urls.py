"""emo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from app01 import views
from django.views.static import serve
from django.conf import settings
import notifications.urls
from django.conf.urls import include

urlpatterns = [
    path('inbox/notifications/', include(notifications.urls, namespace='notifications')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
    path('admin/', admin.site.urls),
    path('come/', views.come),  # 起始页
    path('login/', views.login),  # 用户登录
    path('register/', views.register),  # 用户注册
    path('index/', views.index),  # 进入首页
    path('logout/', views.logout),  # 注销登录（用户和管理员共用）
    path('adminlogin/', views.adminlogin),  # 管理员登录
    path('image/code/', views.image_code),  # 验证码功能
    path('plate_in/', views.plate_in),  # 前端进入分区版块
    path('search/', views.search),  # 前端首页搜索功能
    path('post_in/', views.post_in),  # 进入帖子详情功能
    path('userpage/', views.userpage),  # 进入他人主页功能
    path('mypage/', views.mypage),  # 进入我的个人主页
    path('myfollow/', views.myfollow),  # 我的关注
    path('mycollection/', views.mycollection),  # 我的收藏
    path('chat/', views.chat),  # 进入聊天室
    path('startchat/', views.start_chat),


    # 任务列表
    path('task/like/', views.like),  # 点赞功能
    path('task/collect/', views.collect),  # 收藏功能
    path('task/comment/', views.comment),  # 评论功能
    path('task/post/', views.post),  # 发帖功能
    path('task/follow/', views.follow),  # 关注功能
    path('task/cancel_follow/', views.cancel_follow),  # 取消关注
    path('task/cancel_collection/', views.cancel_collection),  # 取消收藏
    path('task/delete_post/', views.delete_post),  # 删除帖子
    path('task/update_info/', views.update_info),  # 修改个人信息
    path('task/sendmsg/', views.send_msg),  # 发送私信


    # 管理关注表
    path('manage/follow/', views.manage_follow),
    path('manage/follow/delete/', views.delete_follow),

    # 管理收藏表
    path('manage/collection/', views.manage_collection),
    path('manage/collection/add/', views.manage_collection_add),
    path('manage/collection/delete/', views.manage_collection_delete),

    # 管理私信表
    path('manage/message/', views.manage_message),
    path('manage/message/delete/', views.manage_message_delete),

    # 管理板块表
    path('manage/plate/', views.manage_plate),
    path('manage/plate/delete/', views.manage_plate_delete),
    path('manage/plate/<int:nid>/edit/', views.manage_plate_edit),

    # 管理发帖表
    path('manage/post/', views.manage_post),
    path('manage/post/delete/', views.manage_post_delete),
    path('manage/post/<int:nid>/edit/', views.manage_post_edit),

    # 管理用户表
    path('manage/user/', views.manage_user),
    path('manage/user/delete/', views.manage_user_delete),
    path('manage/user/<int:nid>/edit/', views.manage_user_edit),

    # 管理跟帖表
    path('manage/reply/', views.manage_reply),
    path('manage/reply/delete/', views.manage_reply_delete),
    path('manage/reply/<int:nid>/edit/', views.manage_reply_edit),
]
