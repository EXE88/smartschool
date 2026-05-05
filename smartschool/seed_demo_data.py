from datetime import date

from django.contrib.auth.models import User
from django.db import transaction

from basemodels.models import Classes, Grades, Lessons, Students, Subjects, Teachers
from students.models import Student
from teachers.models import Teacher, TeachingAssignment
from weeklyschedules.models import WeeklySchedule

MATH_PROGRAM = [
    ("saturday", ["شیمی", "ورزش", "دینی", "کارآفرینی"]),
    ("sunday", ["حسابان", "عربی", "آمار و احتمال", "فارسی"]),
    ("monday", ["انسان و محیط", "تاریخ معاصر", "فیزیک", "زمین‌شناسی"]),
    ("tuesday", ["حسابان", "هندسه", "شیمی", "آمار و احتمال"]),
    ("wednesday", ["نگارش", "فیزیک", "زبان", "زبان"]),
]

EXPERIMENTAL_PROGRAM = [
    ("saturday", ["شیمی", "ورزش", "دینی", "کارآفرینی"]),
    ("sunday", ["ریاضی", "عربی", "زیست", "فارسی"]),
    ("monday", ["انسان و محیط", "تاریخ معاصر", "فیزیک", "زمین‌شناسی"]),
    ("tuesday", ["ریاضی", "زیست", "شیمی", "ریاضی"]),
    ("wednesday", ["نگارش", "فیزیک", "زبان", "زبان"]),
]

PROGRAMS = {
    "ریاضی": MATH_PROGRAM,
    "تجربی": EXPERIMENTAL_PROGRAM,
}

COMMON_LESSONS = {
    "شیمی",
    "ورزش",
    "دینی",
    "کارآفرینی",
    "عربی",
    "فارسی",
    "انسان و محیط",
    "تاریخ معاصر",
    "فیزیک",
    "زمین‌شناسی",
    "نگارش",
    "زبان",
}

TEACHER_NAMES = {
    "شیمی": ("مریم", "شیمیایی"),
    "ورزش": ("حمید", "ورزنده"),
    "دینی": ("رضا", "معارف"),
    "کارآفرینی": ("سارا", "کارآفرین"),
    "حسابان": ("علی", "حسابی"),
    "عربی": ("فاطمه", "عربی"),
    "آمار و احتمال": ("نیما", "آماری"),
    "فارسی": ("لیلا", "پارسی"),
    "انسان و محیط": ("مهسا", "محیطی"),
    "تاریخ معاصر": ("حسین", "تاریخ‌دان"),
    "فیزیک": ("کاوه", "فیزیکی"),
    "زمین‌شناسی": ("الهام", "زمینی"),
    "هندسه": ("آرمان", "هندسی"),
    "نگارش": ("نگار", "نویسنده"),
    "زبان": ("نرگس", "زبان‌آموز"),
    "ریاضی": ("سمیه", "ریاضی"),
    "زیست": ("بهزاد", "زیستی"),
}

STUDENT_FIRST_NAMES = [
    "امیر", "آراد", "پارسا", "بردیا", "دانیال", "نیما", "سام", "طاها", "کسری", "ماهان",
    "آیلین", "هستی", "رها", "نازنین", "یلدا", "کیمیا", "ملیکا", "ستایش", "درسا", "آتنا",
]

STUDENT_LAST_NAMES = [
    "احمدی", "رضایی", "محمدی", "حسینی", "کریمی", "موسوی", "جعفری", "قاسمی", "اکبری", "مرادی",
    "رحیمی", "صادقی", "کاظمی", "نوری", "شریفی", "رستمی", "صالحی", "عباسی", "مهدوی", "امینی",
]


def normalize_lesson(name):
    return "زیست" if name == "ریست" else name


def next_numeric_username():
    numeric = [int(username) for username in User.objects.values_list("username", flat=True) if username.isdigit()]
    return str(max(numeric, default=0) + 1)


def make_user():
    username = next_numeric_username()
    user = User.objects.create_user(username=username, password=username)
    return user


def get_singletons():
    teachers_list, _ = Teachers.objects.get_or_create(singleton_id=1)
    students_list, _ = Students.objects.get_or_create(singleton_id=1)
    return teachers_list, students_list


def make_teacher(lesson_name, teachers_list):
    username_key = f"demo-teacher-{lesson_name}"
    existing = Teacher.objects.filter(user__first_name=username_key).first()
    if existing:
        teachers_list.teachers.add(existing.user)
        return existing

    first, last = TEACHER_NAMES.get(lesson_name, ("معلم", lesson_name))
    user = make_user()
    user.first_name = username_key
    user.last_name = "seed"
    user.save(update_fields=["first_name", "last_name"])
    teachers_list.teachers.add(user)
    teacher = Teacher.objects.create(
        user=user,
        firstname=first,
        lastname=last,
        birthdate=date(1985, 1, 1),
        nationalcode=f"7{int(user.username):09d}"[-10:],
        phonenumber=f"0912{int(user.username):07d}"[-11:],
    )
    return teacher


def make_student(index, classobj, subject, grade, students_list):
    marker = f"demo-student-{classobj.name}-{index}"
    existing = Student.objects.filter(user__first_name=marker).first()
    if existing:
        students_list.students.add(existing.user)
        return existing

    user = make_user()
    user.first_name = marker
    user.last_name = "seed"
    user.save(update_fields=["first_name", "last_name"])
    students_list.students.add(user)
    name_index = (index - 1) % len(STUDENT_FIRST_NAMES)
    student = Student.objects.create(
        user=user,
        firstname=STUDENT_FIRST_NAMES[name_index],
        lastname=f"{STUDENT_LAST_NAMES[name_index]} {classobj.name}",
        birthdate=date(2008, ((index - 1) % 12) + 1, ((index - 1) % 27) + 1),
        nationalcode=f"8{int(user.username):09d}"[-10:],
        father_phonenumber=f"0913{int(user.username):07d}"[-11:],
        mother_phonenumber=f"0914{int(user.username):07d}"[-11:],
        home_phonenumber=f"021{int(user.username):08d}"[-11:],
        subject=subject,
        grade=grade,
        classobj=classobj,
    )
    return student


def lesson_names_for_program(program):
    return sorted({normalize_lesson(name) for _, periods in program for name in periods})


@transaction.atomic
def seed():
    teachers_list, students_list = get_singletons()
    grade, _ = Grades.objects.get_or_create(name="یازدهم")

    subject_objs = {}
    class_objs = {}
    for subject_name in PROGRAMS:
        subject, _ = Subjects.objects.get_or_create(name=subject_name)
        classobj, _ = Classes.objects.get_or_create(
            name=f"یازدهم {subject_name}",
            defaults={"subject": subject, "grade": grade},
        )
        if classobj.subject_id != subject.id or classobj.grade_id != grade.id:
            classobj.subject = subject
            classobj.grade = grade
            classobj.save()
        subject_objs[subject_name] = subject
        class_objs[subject_name] = classobj

    teacher_by_key = {}
    for subject_name, program in PROGRAMS.items():
        for lesson_name in lesson_names_for_program(program):
            key = lesson_name if lesson_name in COMMON_LESSONS else f"{subject_name}:{lesson_name}"
            teacher_by_key.setdefault(key, make_teacher(lesson_name, teachers_list))

    assignments = {}
    for subject_name, program in PROGRAMS.items():
        subject = subject_objs[subject_name]
        classobj = class_objs[subject_name]
        for lesson_name in lesson_names_for_program(program):
            lesson, _ = Lessons.objects.get_or_create(
                name=lesson_name,
                grade=grade,
                subject=subject,
            )
            teacher_key = lesson_name if lesson_name in COMMON_LESSONS else f"{subject_name}:{lesson_name}"
            assignment, _ = TeachingAssignment.objects.get_or_create(
                classobj=classobj,
                lesson=lesson,
                defaults={"user": teacher_by_key[teacher_key]},
            )
            if assignment.user_id != teacher_by_key[teacher_key].id:
                assignment.user = teacher_by_key[teacher_key]
                assignment.save()
            teacher_by_key[teacher_key].teachingassignments.add(assignment)
            assignments[(subject_name, lesson_name)] = assignment

    for subject_name, program in PROGRAMS.items():
        classobj = class_objs[subject_name]
        for weekday, periods in program:
            schedule, _ = WeeklySchedule.objects.get_or_create(
                classobj=classobj,
                weekday=weekday,
            )
            for period_index, lesson_name in enumerate(periods, start=1):
                setattr(schedule, f"period_{period_index}", assignments[(subject_name, normalize_lesson(lesson_name))])
            schedule.save()

    for subject_name in PROGRAMS:
        for index in range(1, 11):
            make_student(index, class_objs[subject_name], subject_objs[subject_name], grade, students_list)

    print("Seed completed")
    print(f"Users: {User.objects.count()}")
    print(f"Teachers: {Teacher.objects.count()}")
    print(f"Students: {Student.objects.count()}")
    print(f"Teaching assignments: {TeachingAssignment.objects.count()}")
    print(f"Weekly schedules: {WeeklySchedule.objects.count()}")


seed()
