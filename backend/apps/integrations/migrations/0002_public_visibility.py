from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('integrations', '0001_initial')]
    operations = [migrations.AddField(model_name='embeddedpage', name='publicly_visible', field=models.BooleanField(default=False))]
