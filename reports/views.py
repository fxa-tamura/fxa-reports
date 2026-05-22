from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.core.mail import send_mail
from io import BytesIO
from django.core.mail import EmailMessage
from urllib.parse import quote

# ReportLab
import os
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.lib.units import mm

# Local
from .forms import ReportForm, SignUpForm
from .models import Report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

font_path = os.path.join(
    BASE_DIR,
    'reports',
    'fonts',
    'NotoSansJP-Regular.ttf'
)

if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('NotoSansJP', font_path))
    PDF_FONT = 'NotoSansJP'
else:
    PDF_FONT = 'Helvetica'

def build_report_pdf(report):
    buffer = BytesIO()

    styles = getSampleStyleSheet()

    normal_style = styles['Normal']
    normal_style.fontName = PDF_FONT
    normal_style.fontSize = 10
    normal_style.leading = 18
    normal_style.wordWrap = 'CJK'

    summary_text = (report.summary or '')
    summary_text = summary_text.replace('\r\n', '\n').replace('\r', '')
    summary_text = summary_text.replace('\n', '<br/>')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    elements = []

    total_width = 180 * mm

    title_table = Table(
        [['在宅勤務日報']],
        colWidths=[total_width]
    )
    title_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(title_table)

    info_data = [[
        '所属', report.department or '',
        '氏名', report.employee_name or ''
    ]]
    info_table = Table(
        info_data,
        colWidths=[20 * mm, 70 * mm, 20 * mm, 70 * mm]
    )
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('LEFTPADDING', (3, 0), (3, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    weekday_map = ['月', '火', '水', '木', '金', '土', '日']
    d = report.work_date
    date_text = f'R{d.year - 2018}年　{d.month}月　{d.day}日（ {weekday_map[d.weekday()]} 曜日）'

    date_table = Table(
        [[date_text]],
        colWidths=[total_width]
    )
    date_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(date_table)

    task_text = (
        f'・{report.task1 or ""}\n'
        f'・{report.task2 or ""}\n'
        f'・{report.task3 or ""}'
    )

    body_data = [
        ['目標', report.goal or ''],
        ['タスク', task_text],
        ['業務内容', '時間', '業務詳細'],
        ['', report.work_time1 or '', report.work_detail1 or ''],
        ['', report.work_time2 or '', report.work_detail2 or ''],
        ['', report.work_time3 or '', report.work_detail3 or ''],
        ['', report.work_time4 or '', report.work_detail4 or ''],
        ['総括', Paragraph(summary_text, normal_style)],
    ]

    body_table = Table(
        body_data,
        colWidths=[20 * mm, 30 * mm, 130 * mm],
        rowHeights=[None, 22 * mm, None, None, None, None, None, 45 * mm]
    )
    body_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (2, 0)),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('SPAN', (1, 1), (2, 1)),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('SPAN', (0, 2), (0, 6)),
        ('ALIGN', (0, 2), (0, 6), 'CENTER'),
        ('ALIGN', (1, 2), (2, 2), 'CENTER'),
        ('SPAN', (1, 7), (2, 7)),
        ('ALIGN', (0, 7), (0, 7), 'CENTER'),
        ('LEFTPADDING', (1, 0), (-1, -1), 8),
        ('RIGHTPADDING', (1, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(body_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

@login_required
def report_list(request):
    if request.user.is_superuser:
        reports = Report.objects.all()
    else:
        reports = Report.objects.filter(author=request.user, is_deleted=False)

    reports = reports.order_by('-work_date')

    paginator = Paginator(reports, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/report_list.html', {
        'page_obj': page_obj
    })


@login_required
def report_update(request, pk):
    if request.user.is_superuser:
        report = get_object_or_404(Report, pk=pk)
    else:
        report = get_object_or_404(Report, pk=pk, author=request.user)

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            updated_report = form.save(commit=False)
            updated_report.author = report.author
            updated_report.save()
            return redirect('report_list')
    else:
        form = ReportForm(instance=report)

    return render(request, 'reports/report_update.html', {
        'form': form,
        'report': report,
    })


@login_required
def report_delete(request, pk):

    # デモ管理者は削除禁止
    if request.user.username == 'demo_admin':
        messages.error(
            request,
            'デモ管理者は削除できません。'
        )
        return redirect('admin_report_list')

    if request.user.is_staff:
        report = get_object_or_404(Report, pk=pk)
    else:
        report = get_object_or_404(Report, pk=pk, author=request.user)

    if request.method == 'POST':

        if request.user.is_staff:
            # 物理削除
            report.delete()
            return redirect('admin_report_list')
        else:
            # 論理削除
            report.is_deleted = True
            report.save()
            return redirect('report_list')

    return render(request, 'reports/report_delete.html', {
        'report': report
    })


@login_required
def report_create(request):
    if request.user.is_staff:
        return redirect('admin_report_list')

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            print("OK")
            report = form.save(commit=False)
            report.author = request.user
            report.save()

            # admins = User.objects.filter(is_staff=True).exclude(email='')
            # emails = [user.email for user in admins]
            # print(emails)



            # pdf_data = build_report_pdf(report)

            # subject = '【FXA日報アプリ】日報が登録されました'
            # message = (
            #     f'新しい日報が登録されました。\n\n'
            #     f'登録者: {request.user.username}\n'
            #     f'登録者メール: {request.user.email}\n'
            #     f'作業日: {report.work_date}\n'
            #     f'所属: {report.department}\n'
            #     f'氏名: {report.employee_name}\n'
            #     f'目標: {report.goal}\n'
            #     f'総括: {report.summary}\n'
            # )

            # email = EmailMessage(
            #     subject=subject,
            #     body=message,
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     to=emails,
            #     reply_to=[request.user.email] if request.user.email else [],
            # )

           # email.attach(
               # filename=f'report_{report.pk}.pdf',
               # content=pdf_data,
               # mimetype='application/pdf'
            # )

            # email.send(fail_silently=False)

            return redirect('report_list')

        else:
            print(form.errors)

    else:
        form = ReportForm()

    return render(request, 'reports/report_create.html', {
        'form': form
    })

@login_required
def admin_report_list(request):

    if not request.user.is_staff:
        raise PermissionDenied

    reports = Report.objects.all().order_by('-work_date')

    user_id = request.GET.get('user')
    if user_id:
        reports = reports.filter(author__id=user_id)

    paginator = Paginator(reports, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    users = User.objects.all()

    return render(request, 'reports/admin_report_list.html', {
        'page_obj': page_obj,
        'users': users
    })

@login_required
def admin_user_list(request):

    if not request.user.is_staff:
        raise PermissionDenied

    users = User.objects.all().order_by('username')

@staff_member_required
def report_pdf(request, pk):
    report = get_object_or_404(Report, pk=pk)

    response = HttpResponse(content_type='application/pdf')

    filename = f'{report.work_date.strftime("%Y%m%d")}_在宅日報.pdf'
    encoded_filename = quote(filename)

    response['Content-Disposition'] = (
        f"inline; filename*=UTF-8''{encoded_filename}"
    )
    

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    elements = []

    styles = getSampleStyleSheet()

    normal_style = styles['Normal']
    normal_style.fontName = PDF_FONT
    normal_style.fontSize = 10
    normal_style.leading = 18
    normal_style.wordWrap = 'CJK'

    summary_text = (report.summary or '')
    summary_text = summary_text.replace('\r\n', '\n').replace('\r', '')
    summary_text = summary_text.replace('\n', '<br/>')

    def to_paragraph(text):
        text = text or ''
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '')
        text = text.replace('\n', '<br/>')
        return Paragraph(text, normal_style)

    # ==========
    # 共通幅
    # ==========
    total_width = 180 * mm

    # =========================
    # 1. タイトル
    # =========================
    title_table = Table(
        [['在宅勤務日報']],
        colWidths=[total_width]
    )
    title_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(title_table)

    # =========================
    # 2. 所属・氏名
    # =========================
    info_data = [[
        '所属', report.department or '',
        '氏名', report.employee_name or ''
    ]]
    info_table = Table(
        info_data,
        colWidths=[20 * mm, 70 * mm, 20 * mm, 70 * mm]
    )
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
        ('LEFTPADDING', (3, 0), (3, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    # =========================
    # 3. 日付帯
    # =========================
    weekday_map = ['月', '火', '水', '木', '金', '土', '日']
    d = report.work_date
    date_text = f'R{d.year - 2018}年　{d.month}月　{d.day}日（ {weekday_map[d.weekday()]} 曜日）'

    date_table = Table(
        [[date_text]],
        colWidths=[total_width]
    )
    date_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(date_table)

    # =========================
    # 4. 本文
    # =========================
    task_text = (
        f'・{report.task1 or ""}\n'
        f'・{report.task2 or ""}\n'
        f'・{report.task3 or ""}'
    )

    body_data = [
        ['目標', to_paragraph(report.goal)],
        ['タスク', to_paragraph(task_text)],
        ['業務内容', '時間', '業務詳細'],
        ['', report.work_time1 or '', to_paragraph(report.work_detail1)],
        ['', report.work_time2 or '', to_paragraph(report.work_detail2)],
        ['', report.work_time3 or '', to_paragraph(report.work_detail3)],
        ['', report.work_time4 or '', to_paragraph(report.work_detail4)],
        ['総括', to_paragraph(report.summary)],
    ]

    body_table = Table(
        body_data,
        colWidths=[20 * mm, 30 * mm, 130 * mm],
        rowHeights=[
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    )

    body_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1.2, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), PDF_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        ('SPAN', (1, 0), (2, 0)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (0, 2), (0, 6)),
        ('SPAN', (1, 7), (2, 7)),

        ('ALIGN', (0, 0), (0, 7), 'CENTER'),
        ('ALIGN', (1, 2), (2, 2), 'CENTER'),

        ('LEFTPADDING', (1, 0), (-1, -1), 8),
        ('RIGHTPADDING', (1, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(body_table)
    doc.build(elements)
    return response

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('login')

    else:
        form = SignUpForm()

    return render(request, 'reports/signup.html', {
        'form': form
    })


def user_select(request):
    return render(request, 'reports/user_select.html')


class ReportLoginView(LoginView):
    template_name = 'reports/login.html'

    def form_valid(self, form):
        user = form.get_user()

        if user.is_staff:
            logout(self.request)

            messages.error(
                self.request,
                '管理者は管理者ログイン画面からログインしてください。'
            )

            return redirect('admin_login')

        return super().form_valid(form)

    def get_success_url(self):
        return '/reports/list/'
    
class AdminLoginView(LoginView):
    template_name = 'reports/admin_login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            return redirect('report_list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return '/reports/admin-list/'  # 管理者一覧へ

class AdminLogoutView(LogoutView):
    next_page = '/reports/admin-login/'

class ReportLogoutView(LogoutView):
    next_page = '/reports/login/'