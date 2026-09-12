from django.db import migrations, models


def add_deployment_host(apps, schema_editor):
    Server = apps.get_model('servers', 'Server')
    Server.objects.filter(provider='mock', is_primary=True).update(is_primary=False)
    if not Server.objects.filter(provider='local').exists():
        Server.objects.create(name='Deployment host', provider='local', is_primary=not Server.objects.filter(is_primary=True).exists(), description='The machine running Research OS', capabilities=['Monitoring'], enabled=True)


class Migration(migrations.Migration):
    dependencies = [('servers', '0003_alter_server_port')]
    operations = [
        migrations.AlterField(model_name='server', name='provider', field=models.CharField(choices=[('local', 'Deployment host'), ('mock', 'Mock'), ('ssh', 'SSH'), ('xui', '3x-ui')], default='mock', max_length=12)),
        migrations.RunPython(add_deployment_host, migrations.RunPython.noop),
    ]
