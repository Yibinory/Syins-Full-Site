"""A narrow file-based bridge; the API never executes Docker or host commands."""
import json
import os
from pathlib import Path
import time
import uuid
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response


class DeploymentOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_superuser)


class PortChange(serializers.Serializer):
    appPort = serializers.IntegerField(min_value=1024, max_value=65535)
    databasePort = serializers.IntegerField(min_value=1024, max_value=65535, allow_null=True)

    def validate(self, attrs):
        if attrs['appPort'] == attrs['databasePort']:
            raise serializers.ValidationError('Website and database ports must be different.')
        return attrs


def control_directory():
    return Path(os.environ.get('DEPLOYMENT_CONTROL_DIR', '/app/data/deployment'))


def deployment_state():
    try:
        state = json.loads((control_directory() / 'status.json').read_text())
        return {key: state.get(key) for key in ('version', 'current', 'job', 'error')} | {
            'online': 0 <= time.time() - state.get('heartbeat', 0) < 15,
        }
    except (OSError, ValueError, TypeError):
        return {'online': False, 'current': None, 'job': None, 'error': ''}


@api_view(['GET', 'POST'])
@permission_classes([DeploymentOwner])
def deployment_settings(request):
    state = deployment_state()
    if request.method == 'GET':
        return Response(state)
    serializer = PortChange(data=request.data)
    serializer.is_valid(raise_exception=True)
    if not state['online'] or state.get('error'):
        return Response({'detail': 'Deployment manager is unavailable. Start it on the host.'}, status=503)
    if (state.get('job') or {}).get('status') in {'checking', 'applying', 'recovery_required'}:
        return Response({'detail': 'A deployment change is already pending or requires recovery.'}, status=409)
    directory = control_directory()
    identifier = str(uuid.uuid4())
    temporary = directory / (identifier + '.tmp')
    target = directory / 'request.json'
    try:
        with open(temporary, 'x', encoding='utf-8') as stream:
            json.dump({'id': identifier, 'ports': serializer.validated_data}, stream)
        temporary.chmod(0o644)
        # Link a complete file atomically; unlike replace(), this cannot overwrite a pending request.
        os.link(temporary, target)
    except FileExistsError:
        return Response({'detail': 'A deployment change is already pending.'}, status=409)
    except OSError:
        return Response({'detail': 'Deployment control directory is not writable.'}, status=503)
    finally:
        temporary.unlink(missing_ok=True)
    return Response({'id': identifier, 'status': 'queued', 'ports': serializer.validated_data}, status=status.HTTP_202_ACCEPTED)
