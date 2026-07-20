from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Report(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(default=False)
    department = models.CharField('所属', max_length=100, blank=True)
    employee_name = models.CharField('氏名', max_length=100, blank=True)
    work_date = models.DateField('作業日')
    goal = models.CharField('目標', max_length=255, blank=True)

    task1 = models.CharField('タスク1', max_length=255, blank=True)
    task2 = models.CharField('タスク2', max_length=255, blank=True)
    task3 = models.CharField('タスク3', max_length=255, blank=True)

    work_time1 = models.CharField('時間1', max_length=50, blank=True)
    work_detail1 = models.CharField('業務詳細1', max_length=255, blank=True)

    work_time2 = models.CharField('時間2', max_length=50, blank=True)
    work_detail2 = models.CharField('業務詳細2', max_length=255, blank=True)

    work_time3 = models.CharField('時間3', max_length=50, blank=True)
    work_detail3 = models.CharField('業務詳細3', max_length=255, blank=True)

    work_time4 = models.CharField('時間4', max_length=50, blank=True)
    work_detail4 = models.CharField('業務詳細4', max_length=255, blank=True)

    summary = models.TextField('総括', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.work_date} / {self.employee_name or "日報"}'

class SkillSheet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='ユーザー'
    )

    name = models.CharField('氏名', max_length=100)
    kana = models.CharField('フリガナ', max_length=100, blank=True)
    birth_date = models.DateField('生年月日', null=True, blank=True)
    age = models.IntegerField('年齢', null=True, blank=True)
    gender = models.CharField('性別', max_length=20, blank=True)
    nearest_station = models.CharField('最寄駅', max_length=100, blank=True)
    education = models.CharField('最終学歴', max_length=255, blank=True)
    qualification = models.TextField('資格', blank=True)
    self_pr = models.TextField('自己PR', blank=True)

    skill_summary = models.TextField('スキル概要', blank=True)
    career_summary = models.TextField('経歴概要', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.name


class Career(models.Model):
    skill_sheet = models.ForeignKey(
        SkillSheet,
        on_delete=models.CASCADE,
        related_name='careers',
        verbose_name='スキルシート'
    )

    number = models.IntegerField('No.', default=1)
    project_name = models.CharField('案件名・業務名', max_length=255, blank=True)
    work_detail = models.TextField('作業内容', blank=True)
    role = models.CharField('役割', max_length=100, blank=True)
    phase = models.CharField('工程', max_length=255, blank=True)
    os = models.CharField('OS', max_length=255, blank=True)
    language = models.CharField('言語', max_length=255, blank=True)
    database = models.CharField('DB', max_length=255, blank=True)
    tools = models.CharField('ツール', max_length=255, blank=True)
    start_date = models.DateField('開始日', null=True, blank=True)
    end_date = models.DateField('終了日', null=True, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return f'{self.number}: {self.project_name}'