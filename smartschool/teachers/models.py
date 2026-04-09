from django.core.exceptions import ValidationError
from django.db import models
from basemodels.models import Classes, Lessons, Students, Teachers

class TeachingAssignment(models.Model):
    user = models.ForeignKey('auth.user', on_delete=models.CASCADE)
    classobj = models.ForeignKey(Classes, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lessons, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.classobj_id and self.lesson_id:
            if self.lesson.grade_id != self.classobj.grade_id:
                raise ValidationError({"lesson": "Lesson grade must match the selected class grade."})
            if self.lesson.subject_id != self.classobj.subject_id:
                raise ValidationError({"lesson": "Lesson subject must match the selected class subject."})
            if TeachingAssignment.objects.filter(classobj_id=self.classobj_id, lesson_id=self.lesson_id).exclude(pk=self.pk).exists():
                raise ValidationError({"lesson": "This lesson is already assigned to the selected class."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class Teacher(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, unique=True, blank=False)
    firstname = models.CharField(max_length=30, blank=False)
    lastname = models.CharField(max_length=30, blank=False)
    birthdate = models.DateField(blank=False)
    nationalcode = models.CharField(max_length=10, unique=True, blank=False)
    phonenumber = models.CharField(max_length=11, blank=True)
    teachingassignments = models.ManyToManyField('TeachingAssignment', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.user_id:
            teachers_list = Teachers.objects.first()
            if not teachers_list:
                raise ValidationError({"user": "Teachers list is not configured yet."})
            if not teachers_list.teachers.filter(pk=self.user_id).exists():
                raise ValidationError({"user": "Selected user must be in Teachers list."})
            students_list = Students.objects.first()
            if students_list and students_list.students.filter(pk=self.user_id).exists():
                raise ValidationError({"user": "Selected user cannot be in Students list."})
            
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

