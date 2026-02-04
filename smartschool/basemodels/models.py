from django.db import models
from django.core.exceptions import ValidationError

class Subjects(models.Model):
    name = models.CharField(max_length=50, blank=False, unique=True)

    def __str__(self):
        return self.name
    
class Grades(models.Model):
    name = models.CharField(max_length=20, blank=False, unique=True)

    def __str__(self):
        return self.name
    
class Classes(models.Model):
    name = models.CharField(max_length=20, blank=False, unique=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grades, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Lessons(models.Model):
    name = models.CharField(max_length=150, blank=False)
    grade = models.ForeignKey(Grades, on_delete=models.CASCADE, blank=False)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return f"{self.name} - {self.grade} - {self.subject}"

class SingletonModel(models.Model):
    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.__class__.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one instance is allowed for this model.")

    def save(self, *args, **kwargs):
        self.singleton_id = 1
        self.full_clean()
        return super().save(*args, **kwargs)

class Teachers(SingletonModel):
    teachers = models.ManyToManyField('auth.User', related_name='teachers')

    def __str__(self):
        return "Teachers list"

class Students(SingletonModel):
    students = models.ManyToManyField('auth.User', related_name='students')

    def __str__(self):
        return "Students list"
