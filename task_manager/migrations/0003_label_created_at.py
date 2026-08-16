from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('task_manager', '0002_label_task'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AddField(
                    model_name='label',
                    name='created_at',
                    field=models.DateTimeField(null=True),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='label',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True),
                ),
            ],
        ),
    ]
