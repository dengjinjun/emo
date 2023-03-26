from django.db import models


# Create your models here.
class Admin(models.Model):
    """管理员表"""
    username = models.CharField(verbose_name="用户名", max_length=64)
    password = models.CharField(verbose_name="密码", max_length=64)

class UserInfo(models.Model):
    """用户表"""
    username = models.CharField(verbose_name="用户名", max_length=64)
    password = models.CharField(verbose_name="密码", max_length=64)
    gender_choice = (
        (1, "男"),
        (2, "女")
    )
    gender = models.SmallIntegerField(verbose_name="性别", choices=gender_choice)
    age = models.IntegerField(verbose_name="年龄", default=18)
    cell = models.CharField(verbose_name="手机号", null=True, blank=True, max_length=64)
    city = models.CharField(verbose_name="城市", max_length=64, null=True, blank=True)
    photo = models.ImageField(verbose_name="头像", default='head/default.jpg', upload_to='head/')

    def __str__(self):
        return self.username


class Follow(models.Model):
    """关注表"""
    follower = models.ForeignKey(verbose_name='关注人id', to="UserInfo", to_field="id", related_name='+', null=True,
                                 blank=True,
                                 on_delete=models.SET_NULL)
    followed = models.ForeignKey(verbose_name='被关注人id',
                                 to="UserInfo", to_field="id", related_name='+', null=True, blank=True,
                                 on_delete=models.SET_NULL)


class Plate(models.Model):
    """板块表"""
    plate_name = models.CharField(verbose_name="板块名字", max_length=64)
    plate_info = models.TextField(verbose_name="板块介绍")
    plate_logo = models.ImageField(verbose_name="板块logo",upload_to='logo/', null=True, blank=True)
    def __str__(self):
        return self.plate_name

class Post(models.Model):
    """发帖表"""
    poster = models.ForeignKey(verbose_name='发帖人id', to="UserInfo", to_field="id", null=True, blank=True,
                               on_delete=models.SET_NULL)
    plate = models.ForeignKey(verbose_name='板块id', to="Plate", to_field="id", null=True, blank=True,
                              on_delete=models.SET_NULL)
    title = models.CharField(verbose_name="帖头", max_length=128)
    content = models.TextField(verbose_name="帖子内容")
    like = models.BigIntegerField(verbose_name="点赞数", default=0)
    comment = models.DateTimeField(verbose_name="发帖时间", null=True, blank=True, auto_now_add=True)
    image = models.ImageField(verbose_name="帖子图片", upload_to='post/', null=True, blank=True)

    def __str__(self):
        return str(self.id)


class Collection(models.Model):
    """收藏表"""
    collect_er = models.ForeignKey(verbose_name='收藏人', to="UserInfo", to_field="id", null=True, blank=True,
                                   on_delete=models.SET_NULL)
    post = models.ForeignKey(verbose_name='帖子id', to="Post", to_field="id", null=True, blank=True,
                             on_delete=models.SET_NULL)


class Message(models.Model):
    """私信表"""
    sender = models.ForeignKey(verbose_name='发信人id', to="UserInfo", to_field="id", related_name='+', null=True,
                               blank=True,
                               on_delete=models.SET_NULL)
    receiver = models.ForeignKey(verbose_name='收信人id', to="UserInfo", to_field="id", related_name='+', null=True,
                                 blank=True,
                                 on_delete=models.SET_NULL)
    content = models.CharField(verbose_name="信息内容", null=True, blank=True,  max_length=128)
    time = models.DateTimeField(verbose_name="私信时间", auto_now_add=True)


class Reply(models.Model):
    """跟帖表"""
    post = models.ForeignKey(verbose_name='主帖ID', to="Post", to_field="id", null=True, blank=True,
                             on_delete=models.SET_NULL)
    replier = models.ForeignKey(verbose_name='跟帖人', to="UserInfo", to_field="id", null=True, blank=True,
                                on_delete=models.SET_NULL)
    content = models.CharField(verbose_name="跟帖内容", max_length=128)
    time = models.DateTimeField(verbose_name="跟帖时间", auto_now_add=True)
    more = models.ForeignKey(verbose_name='所跟帖数据ID', to="Reply", to_field="id", null=True, blank=True,
                             on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.id)
