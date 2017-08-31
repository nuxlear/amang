import datetime, random

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.core.mail import send_mail

from .models import Schedule, Stack

# Create your views here.
def index(request):
    #schedule_list=Schedule.objects.order_by('start_time')
    request.session['currentid']=None
    daydelta=request.session.get('daydelta',0)
    today=timezone.now()
    now=today+datetime.timedelta(days=daydelta)
    year, weeknum, day = now.isocalendar()
    countlist=[[i,0] for i in range(7)]
    if not daydelta:
        countlist[day-1][1]=1
    startmon = now - datetime.timedelta(days=day-1)
    #startmon = datetime.combine(startmon.date(), datetime.time(0,0,0))
    #startmon.replace(hour=18, minute=0, second=0)
    startday=startmon.date()
    startclock=datetime.time(0,0,0,0)
    startmon=datetime.datetime.combine(startday, startclock)
    #print(startmon, '-', type(startmon))
    weeklist=[]
    dayslist=['월','화','수','목','금','토','일']
    week_schedule=Schedule.objects.filter(start_time__gte=startmon, start_time__lt=startmon+datetime.timedelta(days=7))
    ordered_schedule=week_schedule.order_by('start_time')
    for i in range(7):
        weeklist.append(((startmon+datetime.timedelta(days=i)).date(),dayslist[i]))
    schedule_list=[]
    colorset=[]
    for i in range(1,13):
        colorset.append('color'+str(i))
    #random.shuffle(colorset)
    i=0
    for schedule in week_schedule:
        schedule_time=datetime.datetime.min+(schedule.end_time-schedule.start_time)
        top=schedule.start_time.hour*42+schedule.start_time.minute//3*2-1+schedule.start_time.minute//30
        toph=schedule.start_time.hour*2.6+schedule.start_time.minute/30*1.35
        height=schedule_time.hour*42+schedule_time.minute//3*2
        heighth=schedule_time.hour*2.6+schedule_time.minute/15*1.35
        schedule_list.append((schedule, schedule.start_time.weekday(), (top, toph), (height, heighth), colorset[i]))
        i=(i+1)%12
    stack_list=Stack.objects.all().order_by('-value')
    context={
        "schedule_list":schedule_list,
        "now":now,
        "year":year,
        "weeknum":weeknum,
        "weeklist":weeklist,
        "dayslist":dayslist,
        "week_schedule":week_schedule,
        "countlist":countlist,
        "ordered_schedule":ordered_schedule,
        "stack_list":stack_list,
        }
    return render(request, "timetable/index.html", context)

def new(request):
    context={
        "title":"새 합주",
        "button_value":"✓ 확인",
        "button_name":"add",
    }
    return render(request, "timetable/new.html", context)

def modify(request, schedule_id):
    request.session['currentid']=schedule_id
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    team=schedule.team_name
    date=schedule.start_time.strftime("%Y-%m-%d")
    start=(schedule.start_time+datetime.timedelta(hours=9)).strftime("%H:%M")
    timedelta=schedule.end_time-schedule.start_time
    hour=timedelta.seconds//3600
    minute=(timedelta.seconds//60)%60
    interval="{:02}:{:02}".format(hour,minute)
    context={
        "title":"합주 수정",
        "button_value":"✎ 수정",
        "button_name":"modify",
        "team":team,
        "date":date,
        "start":start,
        "timeop":interval,
    }
    #team date start interval
    return render(request, "timetable/new.html", context)

def delete(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    schedule.delete()
    return HttpResponseRedirect(reverse('timetable:index'))

def add(request):
    if request.POST.get('cancel', False):
        return HttpResponseRedirect(reverse('timetable:index'))
    team = request.POST.get('team', False)
    date = request.POST.get('date', False)
    start = request.POST.get('time', False)
    interval = request.POST.get('interval', False)
    if not( team and date and start and interval):
        messages.info(request, '모든 항목을 작성해 주세요.')
        context={
            "title":"새 합주",
            "button_value":"✓ 확인",
            "button_name":"add",
        }
        return render(request, "timetable/new.html", context)
    hour=0
    minute=0
    if interval in ['t30','t90']:
        minute=30
    if interval in ['t60','t90']:
        hour=1
    if interval=='t120':
        hour=2
    timestr=date+' '+start+'+0900'
    print(timestr)
    stime=parse_datetime(timestr)
    etime=stime+datetime.timedelta(hours=hour, minutes=minute)
    context={
        "team":team,
        "date":date,
        "start":start,
        "interval":interval,
        "timeop":"{:02}:{:02}".format(hour,minute),
        "title":"새 합주",
        "button_value":"✓ 확인",
        "button_name":"add",
    }
    if request.POST.get('add', False):
        schedule = Schedule(team_name=team, start_time=stime, end_time=etime)
    if request.POST.get('modify', False):
        schedule_id=request.session.get('currentid',None)
        if schedule_id==None:
            messages.info(request, '수정할 합주가 없습니다.')
            return render(request, "timetable/new.html", context)
        schedule = get_object_or_404(Schedule, pk=schedule_id)
        schedule.team_name=team
        schedule.start_time=stime
        schedule.end_time=etime
        schedule.save()
        context_add={
            "title":"합주 수정",
            "button_value":"✎ 수정",
            "button_name":"modify",
        }
        context.update(context_add)
        try:
            schedule.save()
        except:
            return HttpResponse("The time is not valid. ")
        return HttpResponseRedirect(reverse('timetable:index'))
    if not schedule.valid_schedule():
        messages.info(request, '유효한 일정을 입력해주세요.')
        return render(request, "timetable/new.html", context)
    if not schedule.is_in_limit():
        messages.info(request, '합주 시간은 2시간을 넘을 수 없습니다.')
        return render(request, "timetable/new.html", context)
    if not schedule.is_collision():
        messages.info(request, '다른 합주와 시간이 겹칩니다.')
        return render(request, "timetable/new.html", context)
    try:
        schedule.save()
    except:
        return HttpResponse("The time is not valid. ")
    return HttpResponseRedirect(reverse('timetable:index'))

def info(request, schedule_id):
    schedule = get_object_or_404(Schedule, pk=schedule_id)
    timedelta=schedule.end_time-schedule.start_time
    hour="{:2}".format(timedelta.seconds//3600)
    minute="{:02}".format((timedelta.seconds//60)%60)
    context={
        "title":"합주 정보",
        "schedule":schedule,
        "hour":hour,
        "minute":minute,
    }
    return render(request, "timetable/info.html", context)

def changeweek(request):
    daydelta=request.session.get('daydelta',0)
    if request.POST.get('prev'):
        daydelta-=7
    elif request.POST.get('next'):
        daydelta+=7
    request.session['daydelta']=daydelta
    return HttpResponseRedirect(reverse('timetable:index'))

# def report(request):
#     send_mail(
#         'Subject here',
#         'Here is the message.',
#         'from@example.com',
#         ['to@example.com'],
#         fail_silently=False,
#     )
#     return HttpResponseRedirect(reverse('timetable:index'))
