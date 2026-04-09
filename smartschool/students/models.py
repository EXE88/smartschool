from django.core.exceptions import ValidationError
from django.db import models
from basemodels.models import Classes, Grades, Subjects, Students, Teachers

class Student(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, unique=True, blank=False)
    firstname = models.CharField(max_length=30, blank=False)
    lastname = models.CharField(max_length=30, blank=False)
    birthdate = models.DateField(blank=False)
    nationalcode = models.CharField(max_length=10, unique=True, blank=False)
    father_phonenumber = models.CharField(max_length=11, blank=True)
    mother_phonenumber = models.CharField(max_length=11, blank=True)
    home_phonenumber = models.CharField(max_length=11, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE, blank=False)
    grade = models.ForeignKey(Grades, on_delete=models.CASCADE, blank=False)
    classobj = models.ForeignKey(Classes, on_delete=models.CASCADE, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.user_id:
            students_list = Students.objects.first()
            if not students_list:
                raise ValidationError({"user": "Students list is not configured yet."})
            if not students_list.students.filter(pk=self.user_id).exists():
                raise ValidationError({"user": "Selected user must be in Students list."})
            teachers_list = Teachers.objects.first()
            if teachers_list and teachers_list.teachers.filter(pk=self.user_id).exists():
                raise ValidationError({"user": "Selected user cannot be in Teachers list."})

        if self.classobj_id:
            if self.subject_id and self.subject_id != self.classobj.subject_id:
                raise ValidationError({"subject": "Subject must match the selected class."})
            if self.grade_id and self.grade_id != self.classobj.grade_id:
                raise ValidationError({"grade": "Grade must match the selected class."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
