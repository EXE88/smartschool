import django.db.models.deletion
from django.db import migrations, models


def copy_user_to_teacher(apps, schema_editor):
    Teacher = apps.get_model("teachers", "Teacher")
    TeachingAssignment = apps.get_model("teachers", "TeachingAssignment")

    user_to_teacher_id = dict(Teacher.objects.values_list("user_id", "id"))
    missing_assignment_ids = []

    for assignment in TeachingAssignment.objects.only("id", "user_id").iterator():
        teacher_id = user_to_teacher_id.get(assignment.user_id)
        if not teacher_id:
            missing_assignment_ids.append(assignment.id)
            continue
        TeachingAssignment.objects.filter(pk=assignment.pk).update(teacher_link_id=teacher_id)

    if missing_assignment_ids:
        ids = ", ".join(str(pk) for pk in missing_assignment_ids)
        raise RuntimeError(
            f"Cannot migrate TeachingAssignment rows without matching Teacher profile. "
            f"Assignment IDs: {ids}"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0002_alter_teachingassignment_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachingassignment',
            name='teacher_link',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='teachers.teacher'),
        ),
        migrations.RunPython(copy_user_to_teacher, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='teachingassignment',
            name='user',
        ),
        migrations.RenameField(
            model_name='teachingassignment',
            old_name='teacher_link',
            new_name='user',
        ),
        migrations.AlterField(
            model_name='teachingassignment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teachers.teacher'),
        ),
    ]
