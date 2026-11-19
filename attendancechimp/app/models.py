"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 





# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class InstructorProfile(models.Model):
    """
    Represents an instructor who teaches courses.
    Each instructor is linked to a Django user account.
    """

    instructor_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    """
    Represents a student who enrolls in courses
    and submits QR codes for attendance.
    Each student is linked to a user account.
    """

    student_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    """
    Represents a course taught by an instructor.
    Each course has one instructor and a meeting schedule.
    An instructor can teach multiple courses.
    """

    course_id = models.AutoField(primary_key=True)
    course_number = models.CharField(max_length=200)
    instructor = models.ForeignKey(
        InstructorProfile,
        on_delete=models.CASCADE
    )
    # One boolean per weekday
    meets_mon = models.BooleanField(default=False)
    meets_tue = models.BooleanField(default=False)
    meets_wed = models.BooleanField(default=False)
    meets_thu = models.BooleanField(default=False)
    meets_fri = models.BooleanField(default=False)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return self.course_number


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    """
    Represents the many-to-many relationship between
    students and courses.
    Each enrollment connects one student to one course.
    """

    enroll_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.student} - {self.course}"


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    """
    Represents a lecture belonging to a course.
    Each lecture has a date and a QR code identifier
    used for attendance tracking.
    """

    lecture_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    qr_id = models.CharField(max_length=100, unique=True
    )

    def __str__(self):
        return f"{self.course} - {self.date}"


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------
class QRCodeUpload(models.Model):
    """
    Represents a QR code photo uploaded by a student.
    Each upload belongs to one student and may be
    associated with a lecture. The image and upload
    timestamp are stored to verify attendance.
    """

    upload_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    image = models.FileField(upload_to="qr_uploads/",
                             null=True,
                             blank=True)

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"QR Upload {self.upload_id} - {self.student}"
# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------





def getUploadsForCourse(course):
    """
    Return the QRCodeUploads that are valid for the course with the given
    course number (e.g. "DATA13600").

    An upload is valid when, in local time (settings.TIME_ZONE):
      a. it was made on a weekday the course meets, and
      b. its time of day is between the course's start_time and end_time.

    Returns an empty list if the course number does not exist.
    """
    from django.utils import timezone

    course_obj = Course.objects.filter(course_number=course).first()
    if course_obj is None:
        return []

    # weekday(): Monday=0 ... Sunday=6; weekends are never meeting days
    meets = [
        course_obj.meets_mon,
        course_obj.meets_tue,
        course_obj.meets_wed,
        course_obj.meets_thu,
        course_obj.meets_fri,
        False,
        False,
    ]

    uploads = QRCodeUpload.objects.filter(lecture__course=course_obj)

    valid = []
    for upload in uploads:
        local = timezone.localtime(upload.uploaded_at)
        if not meets[local.weekday()]:
            continue
        if course_obj.start_time <= local.time() <= course_obj.end_time:
            valid.append(upload)
    return valid
