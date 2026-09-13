from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('content', '0002_localized_content')]
    operations = [
        migrations.AlterField(model_name='siteprofile', name='name', field=models.CharField(default='Research Space', max_length=120)),
        migrations.AlterField(model_name='siteprofile', name='title', field=models.CharField(default='Independent researcher', max_length=180)),
    ]
