
# LLM: ChatGPT (OpenAI GPT-6)
#
# Prompt:
# Generate six Django models for a classroom attendance
# application called AttendanceChimp. Include separate
# instructor and student profiles, courses, enrollments,
# lectures, and QR code uploads. Prioritize data integrity,
# clear relationships, and useful attendance tracking fields.

from django.db import models


class InstructorProfile(models.Model):
    """Stores instructor information and associated courses."""

    instructor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    """Stores student information for enrollment and attendance."""

    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    """Stores courses taught by instructors."""

    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    instructor = models.ForeignKey(
        InstructorProfile,
        on_delete=models.CASCADE,
        related_name="courses"
    )
    meeting_schd = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    """Connects students to courses and prevents duplicate enrollment."""

    enroll_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_enrollment"
            )
        ]


class Lecture(models.Model):
    """Stores individual lectures and unique attendance QR codes."""

    lecture_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    qr_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.course.name} - {self.date}"


class QRCodeUpload(models.Model):
    """Stores student QR uploads and optional lecture associations."""

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
    image = models.ImageField(
        upload_to="qr_uploads/",
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Upload {self.upload_id} by {self.student}"
