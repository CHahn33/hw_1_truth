"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import io

from .models import InstructorProfile, StudentProfile, Course, Enrollment, Lecture, QRCodeUpload, getUploadsForCourse
from django.utils import timezone
CDT = ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""

    context = {
        "user": request.user,
        "current_time": datetime.now(CDT).strftime("%H:%M")
    }
    return render(request, 'app/index.html', context)

def time_view(request):
    current_time = datetime.now(ZoneInfo("America/Chicago"))
    formatted_time = current_time.strftime("%H:%M")
    return HttpResponse(formatted_time, content_type="text/plain")

import json
from django.http import HttpResponse

def sum_view(request):
    n1 = float(request.GET.get("n1"))
    n2 = float(request.GET.get("n2"))

    total = n1 + n2

    return HttpResponse(f"<p>{total}</p>")



# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------
@require_GET

def new(request):
    return render(request, 'app/new.html')

@csrf_exempt
@require_POST
def createUser(request):
    email = request.POST.get("email")
    user_name = request.POST.get("user_name")
    password = request.POST.get("password")
    is_student = request.POST.get("is_student")

    if not email or not user_name or not password or is_student not in ("1", "0", "true", "false"):
        return HttpResponse("Invalid form data", status=400)

    if User.objects.filter(email=email).exists():
        return HttpResponse("Email already exists", status=400)

    if User.objects.filter(username=user_name).exists():
        return HttpResponse("Username already exists", status=400)

    user = User.objects.create_user(
        username=user_name,
        email=email,
        password=password
    )

    if is_student in ("1", "true"):
        StudentProfile.objects.create(user=user, name=user_name)
    else:
        InstructorProfile.objects.create(user=user, name=user_name)

    login(request, user)

    return HttpResponse("User created successfully", status=200)

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------
@login_required
def new_course(request):
    return render(request, 'app/new_course.html')

@csrf_exempt
def createCourse(request):
    if request.method != 'POST':
        return HttpResponse("POST Required", status=405)
    
    if not request.user.is_authenticated:
        return HttpResponse("Instructor Required", status=401)
    
    instructor = InstructorProfile.objects.filter(user=request.user).first()

    if instructor is None:
        return HttpResponse("Instructor Required", status=401)
    course_number = request.POST.get("course-number")
    start_str = request.POST.get("start-time")
    end_str = request.POST.get("end-time")

    days = {
        day: bool(request.POST.get("day-" + day))
        for day in ['mon', 'tue', 'wed', 'thu', 'fri']
    }

    if not course_number or not start_str or not end_str or not any(days.values()):
        return HttpResponse("Missing course data", status=400)

    # Times arrive as 24-hour "HH:MM" strings; convert to time objects
    try:
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
    except ValueError:
        return HttpResponse("Invalid time format", status=400)

    Course.objects.create(
        course_number=course_number,
        instructor=instructor,
        meets_mon=days['mon'],
        meets_tue=days['tue'],
        meets_wed=days['wed'],
        meets_thu=days['thu'],
        meets_fri=days['fri'],
        start_time=start_time,
        end_time=end_time,
    )

    return HttpResponse("Course created successfully", status=200)

@login_required
def new_lecture(request):
    courses = Course.objects.filter(instructor__user=request.user)

    return render(request, 'app/new_lecture.html', {'courses': courses})

@csrf_exempt
def createLecture(request):
    if request.method != 'POST':
        return HttpResponse("POST Required", status=405)
    
    if not request.user.is_authenticated:
        return HttpResponse("Instructor Required", status=401)
    
    instructor = InstructorProfile.objects.filter(user=request.user).first()

    if instructor is None:
        return HttpResponse("Instructor Required", status=401)
    
    course_name = request.POST.get("choice")

    if not course_name:
        return HttpResponse("Missing course number", status=400)

    course = Course.objects.filter(course_number=course_name, instructor=instructor).first()

    if course is None:
        return HttpResponse("Course not found", status=400)
    
    Lecture.objects.create(
        course=course,
        date=datetime.now(CDT).date(),
        qr_id=__import__('uuid').uuid4().hex
    )

    return HttpResponse("Lecture created successfully", status=200)

@login_required
def new_qr_upload(request):
    return render(request, 'app/new_qr_upload.html')

@csrf_exempt
def createQRCodeUpload(request):
    if request.method != 'POST':
        return HttpResponse("POST Required", status=405)
    
    if not request.user.is_authenticated:
        return HttpResponse("Student Required", status=401)
    
    student = StudentProfile.objects.filter(user=request.user).first()

    if student is None:
        return HttpResponse("Student Required", status=401)

    image = request.FILES.get("imageUpload")

    if image is None:
        return HttpResponse("Missing image file", status=400)
    
    QRCodeUpload.objects.create(
        student=student,
        image=image
    )

    return HttpResponse("QR Code uploaded successfully", status=200)

def dumpUploads(request):
    if request.method != 'GET':
        return HttpResponse("GET Required", status=405)
    
    if not request.user.is_authenticated:
        return HttpResponse("Instructor Required", status=401)
    
    instructor = InstructorProfile.objects.filter(user=request.user).first()

    if instructor is None:
        return HttpResponse("Instructor Required", status=401)
    
    uploads = QRCodeUpload.objects.all()

    data = []
    for upload in uploads:
        data.append({
            "username": upload.student.user.username,
            "upload_time": upload.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return JsonResponse(data, safe=False)
# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------

def getUploads(request):
    if request.method != 'GET':
        return HttpResponse("GET Required", status=405)
    
    if not request.user.is_authenticated:
        return HttpResponse("Instructor Required", status=401)
    
    instructor = InstructorProfile.objects.filter(user=request.user).first()

    if instructor is None:
        return HttpResponse("Instructor Required", status=401)
    
    course = request.GET.get("course")

    if not course:
        return JsonResponse({"error": "Missing course parameter"}, status=400)
    
    uploads = getUploadsForCourse(course)

    data = []
    for upload in uploads:
        data.append({
            "username": upload.student.user.username,
            "upload_time": timezone.localtime(upload.uploaded_at).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return JsonResponse(data, safe=False)
