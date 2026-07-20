import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Report
from .models import SkillSheet


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='メールアドレス'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に登録されています。')
        return email


class ReportForm(forms.ModelForm):
    work_date = forms.DateField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Report
        fields = [
            'department',
            'employee_name',
            'work_date',
            'goal',
            'task1', 'task2', 'task3',
            'work_time1', 'work_detail1',
            'work_time2', 'work_detail2',
            'work_time3', 'work_detail3',
            'work_time4', 'work_detail4',
            'summary',
        ]
        widgets = {
            'work_time1': forms.TextInput(attrs={'placeholder': '例: 10:00～11:00'}),
            'work_time2': forms.TextInput(attrs={'placeholder': '例: 10:00～11:00'}),
            'work_time3': forms.TextInput(attrs={'placeholder': '例: 10:00～11:00'}),
            'work_time4': forms.TextInput(attrs={'placeholder': '例: 10:00～11:00'}),
            'summary': forms.Textarea(attrs={'rows': 6}),
        }

    def _validate_work_time_format(self, value):
        if value:
            pattern = r'^([01]\d|2[0-3]):([0-5]\d)～([01]\d|2[0-3]):([0-5]\d)$'
            if not re.match(pattern, value):
                raise forms.ValidationError('10:00～11:00 の形式で入力してください')
        return value

    def clean_work_time1(self):
        return self._validate_work_time_format(self.cleaned_data.get('work_time1'))

    def clean_work_time2(self):
        return self._validate_work_time_format(self.cleaned_data.get('work_time2'))

    def clean_work_time3(self):
        return self._validate_work_time_format(self.cleaned_data.get('work_time3'))

    def clean_work_time4(self):
        return self._validate_work_time_format(self.cleaned_data.get('work_time4'))

class SkillSheetForm(forms.ModelForm):
    birth_date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = SkillSheet

        fields = [
            'name',
            'kana',
            'birth_date',
            'age',
            'gender',
            'nearest_station',
            'education',
            'qualification',
            'self_pr',
            'skill_summary',
            'career_summary',
        ]

        widgets = {
            'qualification': forms.Textarea(attrs={'rows': 4}),
            'self_pr': forms.Textarea(attrs={'rows': 5}),
            'skill_summary': forms.Textarea(attrs={'rows': 5}),
            'career_summary': forms.Textarea(attrs={'rows': 5}),
        }