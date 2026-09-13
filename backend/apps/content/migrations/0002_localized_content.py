from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('content', '0001_initial')]
    operations = [
        migrations.AddField(model_name=name, name='translations', field=models.JSONField(blank=True, default=dict))
        for name in ('siteprofile', 'researchproject', 'currentresearchitem')
    ] + [
        migrations.AddField(model_name='siteprofile', name=name, field=models.TextField(blank=True, default=value))
        for name, value in (
            ('papers_heading', 'Papers worth returning to.'),
            ('papers_description', 'A reading collection on medical imaging, generalization and generation. Recommendations, context and linked notes, newest first.'),
            ('tools_heading', 'Tools & resources.'),
            ('tools_description', 'A collection of useful external pages and research tools.'),
        )
    ]
