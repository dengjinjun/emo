import os.path

from django.contrib import auth
from django.shortcuts import render, redirect, HttpResponse
from app01 import models
from django import forms
from app01.utils import page
from django.core.exceptions import ValidationError
from app01.utils.encrypt import md5
from io import BytesIO
from app01.utils.code import check_code
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q
from notifications.signals import notify
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
import os
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required




# Create your views here.
def send_notifications(actor, verb, recipient, target=None,
                       description=None, **kwargs):
    """
        这里原本放的是上文各个参数的说明
    """
    notify.send(sender=actor,
                recipient=recipient,
                verb=verb,
                target=target,
                description=description,
                **kwargs
                )


# 验证用户登录装饰器
def checkLogin(func):
    def wrapper1(request, *args, **kwargs):
        info = request.session.get('info', False)
        if info:
            username = info.get("username", False)
            if username:
                return func(request, *args, **kwargs)
        else:
            return redirect('/login/')
    return wrapper1

# 验证管理员登录装饰器
def checkadminLogin(func):
    def wrapper(request, *args, **kwargs):
        info = request.session.get('admininfo', False)
        if info:
            username = info.get("username", False)
            if username:
                return func(request, *args, **kwargs)
        else:
            return redirect('/adminlogin/')
    return wrapper

# 进入网站
def come(request):
    return render(request,"come.html")

# 登陆表ModelForm类
class LoginForm(forms.ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ["username", "password"]
        widgets = {
            "password": forms.PasswordInput(render_value=True)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label,}

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

# 用户登录
def login(request):
    if request.method == 'GET':
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user_object = models.UserInfo.objects.filter(**form.cleaned_data).first()
        if not user_object:
            form.add_error("password", "用户名或密码错误")
            return render(request, 'login.html', {'form': form})
        # 验证正确
        request.session["info"] = {'id': user_object.id, 'username': user_object.username, 'password':user_object.password}
        return redirect('/index/')
    return render(request, 'login.html', {'form': form})

# 注销
def logout(request):
    request.session.clear()
    return redirect('/come/')

# 进入首页
def index(request):
    if request.session.get('info'):
        card = 1
    else:
        card = 0
    queryset1 = models.Plate.objects.all()
    queryset2 = models.Post.objects.all().order_by("-like")[:8]
    queryset3 = models.Post.objects.all().order_by("-like")[8:]
    return render(request,'index.html',{'queryset1':queryset1, 'queryset2': queryset2, 'queryset3': queryset3, 'card': json.dumps(card)})

# 首页搜索功能
def search(request):
    if request.session.get('info'):
        card = 1
    else:
        card = 0
    data_dict = {}
    key_word = request.POST.get("key_word")
    if key_word:
        data_dict['title__contains'] = key_word
    queryset3 = models.Post.objects.filter(**data_dict).order_by("-like")
    queryset1 = models.Plate.objects.all()
    queryset2 = models.Post.objects.all().order_by("-like")[:8]
    return render(request, 'index.html', {'queryset1':queryset1, 'queryset2': queryset2, 'queryset3': queryset3, 'key_word': key_word, 'card': json.dumps(card)})

# 进入分区版块
def plate_in(request):
    if request.session.get('info'):
        card = 1
    else:
        card = 0
    nid = request.GET.get('nid')  # 获取到版块id
    queryset1 = models.Plate.objects.all()
    queryset2 = models.Post.objects.all().order_by("-like")[:8]
    queryset3 = models.Post.objects.filter(plate_id=nid).order_by("-like")
    return render(request, 'index.html', {'queryset1':queryset1, 'queryset2': queryset2, 'queryset3': queryset3, 'nid':nid, 'card': json.dumps(card)})

# 进入帖子详情
@checkLogin
def post_in(request):
    nid = request.GET.get('nid')  # 获取到帖子id
    myid = request.session['info']['id']
    flag = models.Collection.objects.filter(collect_er_id=myid, post_id=nid).first()
    if flag:
        is_collect = 1
    else:
        is_collect = 0
    print(nid, myid, flag, is_collect)
    post_obj = models.Post.objects.filter(id=nid).first()
    queryset = models.Reply.objects.filter(post_id=nid).order_by("time")
    return render(request, 'post.html', {'queryset': queryset, 'post_obj': post_obj, 'is_collect':is_collect})

# 进入个人主页
@checkLogin
def mypage(request):
    myid = request.session['info']['id']
    obj = models.UserInfo.objects.filter(id=myid).first()
    num = models.Post.objects.filter(poster_id=myid).count()
    queryset = models.Post.objects.filter(poster_id=myid)
    return render(request, 'mypage.html', {'obj': obj, 'num': num, 'queryset':queryset})

# 删除帖子功能
@checkLogin
def delete_post(request):
    post_id = request.GET.get('nid')
    models.Post.objects.filter(id=post_id).delete()
    return HttpResponse(str(post_id))

# 回复评论功能
@csrf_exempt
@checkLogin
def comment(request):
    pid = request.POST.get('pid')
    print(pid)
    post_id = request.POST.get('post_id')
    post = models.Post.objects.filter(id=post_id).first()
    content = request.POST.get('content')
    replier_id = request.session['info']['id']
    replier = models.UserInfo.objects.filter(id=replier_id).first()
    if pid:
        more = models.Reply.objects.filter(id=pid).first()
        models.Reply.objects.create(replier=replier,content=content, post=post, more=more)
    else:
        models.Reply.objects.create(replier=replier, content=content, post=post)
    return HttpResponse('评论成功', content)

# 聊天室
@checkLogin
def chat(request):
    myid = request.session['info']['id']
    queryset1 = models.Follow.objects.filter(follower_id=myid)  # 我的关注
    queryset2 = models.Follow.objects.filter(followed_id=myid)  # 关注我的
    queryset3 = models.Message.objects.all().order_by('time')
    return render(request, 'chat.html', {'queryset1':queryset1, 'queryset2':queryset2, 'queryset3':queryset3})

# 发起聊天
def start_chat(request):
    myid = request.session['info']['id']
    nid = request.GET.get('nid')
    queryset1 = models.Follow.objects.filter(follower_id=myid)  # 我的关注
    queryset2 = models.Follow.objects.filter(followed_id=myid)  # 关注我的
    queryset = models.Message.objects.filter(Q(receiver_id=myid,sender_id=nid)|Q(receiver_id=nid,sender_id=myid)).order_by('time')
    print(type(nid),type(myid),queryset)
    return render(request, 'chat.html', {'queryset1':queryset1, 'queryset2':queryset2,'queryset':queryset, 'nid':int(nid)})

# 发送私信
def send_msg(request):
    myid = request.session['info']['id']
    nid = request.GET.get('nid')
    content = request.GET.get('text')
    models.Message.objects.create(receiver_id=nid,sender_id=myid,content=content)
    return HttpResponse('收到了')

# 发帖功能
@csrf_exempt
@checkLogin
def post(request):
    poster_id = request.session['info']['id']
    poster = models.UserInfo.objects.filter(id=poster_id).first()
    plate_id = request.POST.get('plate')
    plate = models.Plate.objects.filter(id=plate_id).first()
    title = request.POST.get('title')
    content = request.POST.get('content')
    image = request.FILES['image']
    print(poster, plate, title, content, image)
    models.Post.objects.create(poster=poster, plate=plate, title=title, content=content, image=image)
    return HttpResponse('发布成功')

# 修改个人信息
@csrf_exempt
@checkLogin
def update_info(request):
    myid = request.session['info']['id']
    username = request.POST.get('username')
    password = request.POST.get('password')
    cell = request.POST.get('cell')
    age = request.POST.get('age')
    city = request.POST.get('city')
    photo = request.FILES['image']
    print(photo)
    models.UserInfo.objects.filter(id=myid).update(username=username, password=password, cell=cell, age=age, city=city)
    obj = models.UserInfo.objects.filter(id=myid).first()
    obj.photo = photo
    obj.save()
    return HttpResponse('修改成功')

# 进入他人主页
@checkLogin
def userpage(request):
    uid = request.GET.get('uid')
    myid = request.session['info']['id']
    if int(uid) == myid:
        return redirect('/mypage/')
    flag = models.Follow.objects.filter(follower=myid,followed=uid).first()
    if flag:
        is_follow = 1
    else:
        is_follow = 0
    user_obj = models.UserInfo.objects.filter(id=uid).first()
    num = models.Post.objects.filter(poster_id=uid).count()
    queryset = models.Post.objects.filter(poster_id=uid)
    print("我到这里了")
    return render(request,'userpage.html',{'user_obj':user_obj, 'num':num, 'queryset': queryset, 'is_follow': is_follow})

# 点赞功能
@checkLogin
def like(request):
    nid = request.GET['nid']
    num = models.Post.objects.filter(id=nid).first().like
    models.Post.objects.filter(id=nid).update(like=num+1)
    return HttpResponse("点赞成功")

# 收藏功能
@checkLogin
def collect(request):
    nid = request.GET['nid']
    user_id = request.session["info"]['id']
    models.Collection.objects.get_or_create(collect_er_id=user_id, post_id=nid)
    actor = models.UserInfo.objects.filter(id=user_id).get()
    receive = models.UserInfo.objects.filter(id=nid).first().save()
    print(actor)
    send_notifications(actor, "收藏", receive,
                       description="sp", level="danger")
    return HttpResponse('已收藏')

# 关注功能
@checkLogin
def follow(request):
    uid = request.GET.get('uid')
    myid = request.session['info']['id']
    models.Follow.objects.get_or_create(follower_id=myid, followed_id=uid)
    return HttpResponse('已关注')

# 我的关注
@checkLogin
def myfollow(request):
    myid = request.session['info']['id']
    queryset = models.Follow.objects.filter(follower_id=myid)
    return render(request, 'follow.html', {'queryset': queryset})

# 取消关注
@checkLogin
def cancel_follow(request):
    nid = request.GET.get('nid')
    myid = request.session['info']['id']
    models.Follow.objects.filter(follower_id=myid, followed_id=nid).delete()
    return HttpResponse(str(nid))

# 我的收藏
@checkLogin
def mycollection(request):
    myid = request.session['info']['id']
    queryset = models.Collection.objects.filter(collect_er_id=myid)
    return render(request, 'collection.html', {'queryset':queryset})

# 取消收藏
@checkLogin
def cancel_collection(request):
    post_id = request.GET.get('nid')
    myid = request.session['info']['id']
    models.Collection.objects.filter(collect_er_id=myid, post_id=post_id).delete()
    return HttpResponse(str(post_id))

# 管理员表ModelForm类
class AdminForm(forms.ModelForm):
    code = forms.CharField(label="验证码", widget=forms.TextInput, required=True)
    class Meta:
        model = models.Admin
        fields = ["username", "password", "code"]
        widgets = {
            "password": forms.PasswordInput(render_value=True)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label}

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

# 管理员登录
def adminlogin(request):
    if request.method == 'GET':
        form = AdminForm()
        return render(request, 'adminlogin.html', {'form': form})
    form = AdminForm(data=request.POST)
    if form.is_valid():
        user_input_code = form.cleaned_data.pop("code")
        code = request.session.get("image_code", "")
        if code.upper() != user_input_code.upper():
            form.add_error("code", "验证码错误")
            return render(request, 'adminlogin.html', {'form':form})

        user_object = models.Admin.objects.filter(**form.cleaned_data).first()
        if not user_object:
            form.add_error("password", "用户名或密码错误")
            return render(request, 'adminlogin.html', {'form': form})
        # 验证正确
        request.session["info"] = {'id': user_object.id, 'username': user_object.username}
        return redirect('/manage/user/')
    return render(request, 'adminlogin.html', {'form': form})

# 验证码功能
def image_code(request):
    img, code_string = check_code()
    request.session['image_code'] = code_string
    request.session.set_expiry(60)
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())

# 管理关注表整合添加关注功能

def manage_follow(request):
    """管理关注表"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.Follow.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=5,
                                  )
    page_html = page_object.page_html()
    ### 分页组件 ###
    if request.method == 'GET':
        query_set = models.Follow.objects.all()[page_object.start:page_object.end]
        return render(request, 'follow_table.html', {'queryset': query_set,'page_html': page_html})
    follower = models.UserInfo.objects.filter(id=request.POST.get("follower")).first()
    followed = models.UserInfo.objects.filter(id=request.POST.get("followed")).first()
    print(follower, followed)
    models.Follow.objects.create(follower=follower, followed=followed)
    query_set = models.Follow.objects.all()[page_object.start:page_object.end]
    return render(request, 'follow_table.html', {'queryset': query_set,'page_html': page_html})

# 删除关注

def delete_follow(request):
    """删除关注"""
    nid = request.GET.get('nid')
    models.Follow.objects.filter(id=nid).delete()
    return redirect('/manage/follow/')

# 收藏表ModelForm类
class CollectionForm(forms.ModelForm):
    """收藏表ModelForm"""

    class Meta:
        model = models.Collection
        fields = ["collect_er", "post"]  # 里面是字段名

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label,}

# 管理收藏表

def manage_collection(request):
    """管理收藏表"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.Collection.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=5,
                                  )
    page_html = page_object.page_html()
    ### 分页组件 ###
    query_set = models.Collection.objects.all()[page_object.start:page_object.end]
    if request.method == 'GET':
        form = CollectionForm()
        return render(request, 'collection_table.html', {'query_set': query_set, 'form': form, 'page_html': page_html})
    return render(request, 'collection_table.html', {'query_set': query_set})

# 添加收藏

def manage_collection_add(request):
    """添加收藏"""
    query_set = models.Collection.objects.all()
    form = CollectionForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('/manage/collection/')
    return render(request, 'collection_table.html', {'query_set': query_set, 'form': form})

# 删除收藏

def manage_collection_delete(request):
    """删除收藏"""
    nid = request.GET.get('nid')
    models.Collection.objects.filter(id=nid).delete()
    return redirect('/manage/collection/')

# 管理私信表,整合搜索功能

def manage_message(request):
    """管理私信表,整合搜索功能"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.Message.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=5,
                                  )
    page_html = page_object.page_html()
    ### 分页组件 ###
    if request.method == 'GET':
        query_set = models.Message.objects.all()[page_object.start:page_object.end]
        return render(request, 'message_table.html', {'query_set': query_set, 'page_html':page_html})
    data_dict = {}
    key_word = request.POST.get("key_word")
    if key_word:
        data_dict['content__contains'] = key_word
    query_set = models.Message.objects.filter(**data_dict)[page_object.start:page_object.end]
    return render(request, 'message_table.html', {'query_set': query_set,'key_word':key_word, 'page_html':page_html})

# 删除私信

def manage_message_delete(request):
    """删除私信"""
    nid = request.GET.get('nid')
    models.Message.objects.filter(id=nid).delete()
    return redirect('/manage/message/')

# 版块表ModelForm类
class PlateForm(forms.ModelForm):
    """版块表ModelForm"""
    class Meta:
        model = models.Plate
        fields = ["plate_name", "plate_info", "plate_logo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label}

# 管理板块表整合添加版块功能

def manage_plate(request):
    """管理板块表"""
    query_set = models.Plate.objects.all()

    if request.method == 'GET':
        form = PlateForm()
        return render(request, 'plate_table.html', {'query_set': query_set, 'form': form})
    form = PlateForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        form = PlateForm()
        return render(request, 'plate_table.html', {'query_set': query_set,'form': form})
    return render(request, 'collection_table.html', {'query_set': query_set, 'form': form})

# 删除版块

def manage_plate_delete(request):
    """删除版块"""
    nid = request.GET.get('nid')
    models.Plate.objects.filter(id=nid).delete()
    return redirect('/manage/plate/')

# 编辑版块

def manage_plate_edit(request, nid):
    """编辑版块"""
    query_set = models.Plate.objects.all()
    row_object = models.Plate.objects.filter(id=nid).first()
    if request.method == 'GET':
        form = PlateForm(instance=row_object)
        return render(request, 'plate_edit.html', {'query_set': query_set, 'form': form})
    form = PlateForm(data=request.POST, files=request.FILES, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/manage/plate/')
    return render(request, 'plate_edit.html', {'query_set': query_set, 'form': form})

# 发帖表ModelForm类
class PostForm(forms.ModelForm):
    """发帖表ModelForm"""
    class Meta:
        model = models.Post
        fields = ["poster", "plate", "title", "content", "like", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label,"autocomplete":"off"}

# 管理发帖表整合添加帖子功能

def manage_post(request):
    """管理帖子"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.Post.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=6,
                                  )
    page_html = page_object.page_html()
    query_set = models.Post.objects.all()[page_object.start:page_object.end]
    if request.method == 'GET':
        form = PostForm()
        return render(request, 'post_table.html', {'query_set': query_set, 'form': form,'page_html':page_html})
    form = PostForm(data=request.POST,files=request.FILES)
    if form.is_valid():
        form.save()
        form = PostForm()
        return render(request, 'post_table.html', {'query_set': query_set,'form': form, 'page_html':page_html})
    return render(request, 'post_table.html', {'query_set': query_set, 'form': form, 'page_html':page_html})

# 删除帖子

def manage_post_delete(request):
    """删除帖子"""
    nid = request.GET.get('nid')
    models.Post.objects.filter(id=nid).delete()
    return redirect('/manage/post/')

# 编辑帖子

def manage_post_edit(request,nid):
    """编辑帖子"""
    query_set = models.Post.objects.all()
    row_object = models.Post.objects.filter(id=nid).first()
    if request.method == 'GET':
        form = PostForm(instance=row_object)
        return render(request, 'post_edit.html', {'query_set': query_set, 'form': form})
    form = PostForm(data=request.POST, files=request.FILES, instance=row_object)
    if form.is_valid():
        print(request.FILES)
        form.save()
        return redirect('/manage/post/')
    return render(request, 'post_edit.html', {'query_set': query_set, 'form': form})

# 用户表ModelForm类
class UserForm(forms.ModelForm):
    """用户表ModelForm"""
    class Meta:
        model = models.UserInfo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control",  "autocomplete":"off"}

# 管理用户表整合添加用户功能

def manage_user(request):
    """管理用户表"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.UserInfo.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=5,
                                  )
    page_html = page_object.page_html()
    query_set = models.UserInfo.objects.all()[page_object.start:page_object.end]
    if request.method == 'GET':
        form = UserForm()
        return render(request, 'user_table.html', {'query_set': query_set, 'form': form, 'page_html':page_html})
    form = UserForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        form.save()
        form = UserForm()
        return render(request, 'user_table.html', {'query_set': query_set, 'form': form, 'page_html':page_html})
    return render(request, 'user_table.html', {'query_set': query_set, 'form': form, 'page_html':page_html})

# 删除用户

def manage_user_delete(request):
    """删除用户"""
    nid = request.GET.get('nid')
    models.UserInfo.objects.filter(id=nid).delete()
    return redirect('/manage/user/')

# 编辑用户

def manage_user_edit(request,nid):
    """编辑用户"""
    query_set = models.UserInfo.objects.all()
    row_object = models.UserInfo.objects.filter(id=nid).first()
    if request.method == 'GET':
        form = UserForm(instance=row_object)
        return render(request, 'user_edit.html', {'query_set': query_set, 'form': form})
    form = UserForm(data=request.POST, files=request.FILES, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/manage/user/')
    return render(request, 'user_edit.html', {'query_set': query_set, 'form': form})

# 跟帖表ModelForm类
class ReplyForm(forms.ModelForm):
    """跟帖表ModelForm"""

    class Meta:
        model = models.Reply
        fields = ["post", "replier", "content", "more"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label,"autocomplete":"off"}

# 管理跟帖表整合添加跟帖功能

def manage_reply(request):
    """管理跟帖表"""
    current_page = request.GET.get('page', 1)
    page_object = page.Pagination(current_page=current_page,
                                  all_count=models.Reply.objects.all().count(),
                                  base_url=request.path_info,
                                  query_params=request.GET,
                                  per_page=6,
                                  )
    page_html = page_object.page_html()
    query_set = models.Reply.objects.all()[page_object.start:page_object.end]
    if request.method == 'GET':
        form = ReplyForm()
        return render(request, 'reply_table.html', {'query_set': query_set, 'form': form, 'page_html': page_html})
    form = ReplyForm(data=request.POST)
    if form.is_valid():
        form.save()
        form = ReplyForm()
        return render(request, 'reply_table.html', {'query_set': query_set, 'form': form, 'page_html': page_html})
    return render(request, 'reply_table.html', {'query_set': query_set, 'form': form, 'page_html': page_html})

# 删除跟帖

def manage_reply_delete(request):
    """删除跟帖"""
    nid = request.GET.get('nid')
    models.Reply.objects.filter(id=nid).delete()
    return redirect('/manage/reply/')

# 编辑跟帖

def manage_reply_edit(request,nid):
    """编辑跟帖"""
    query_set = models.Reply.objects.all()
    row_object = models.Reply.objects.filter(id=nid).first()
    if request.method == 'GET':
        form = ReplyForm(instance=row_object)
        return render(request, 'reply_edit.html', {'query_set': query_set, 'form': form})
    form = ReplyForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()
        return redirect('/manage/reply/')
    return render(request, 'reply_edit.html', {'query_set': query_set, 'form': form})

# 注册表ModelForm类
class RegisterForm(forms.ModelForm):
    """注册表ModelForm"""
    confirm_pwd = forms.CharField(label="确认密码", widget=forms.PasswordInput,)
    class Meta:
        model = models.UserInfo
        fields = ["username", "cell", "password", "confirm_pwd","gender"]
        widgets= {
            "password":forms.PasswordInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label, "autocomplete":"off"}

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

    def clean_confirm_pwd(self):
        pwd = self.cleaned_data.get("password")
        confirm = md5(self.cleaned_data.get("confirm_pwd"))
        if confirm != pwd:
            raise ValidationError("密码不一致，请重新输入！")
        return confirm

# 注册
def register(request):
    form = RegisterForm
    if request.method == 'GET':
        return render(request, 'register.html', {'form': form})
    form = RegisterForm(data=request.POST)
    print(request.POST)
    if form.is_valid():
        form.save()
        return redirect('/login/')
    return render(request, 'register.html', {'form': form})

