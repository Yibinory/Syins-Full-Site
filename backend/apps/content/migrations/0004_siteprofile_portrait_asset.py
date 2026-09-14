from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("content", "0003_generic_profile_defaults")]
    operations = [migrations.AddField(model_name="siteprofile", name="portrait_asset", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="portraits", to="core.mediaasset"))]
