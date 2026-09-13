from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import SiteProfile


class LocalizedContentTests(TestCase):
    def test_nested_translations_and_empty_english_roundtrip(self):
        client = APIClient()
        client.force_authenticate(get_user_model().objects.create_user(username='content-test'))
        payload = {
            'name': '', 'translations': {'zh': {'name': '研究者'}},
            'papersHeading': '', 'toolsHeading': 'Tools',
            'selectedProjects': [{'title': '', 'status': '', 'mediaType': 'image', 'mediaUrl': '', 'mediaAlt': '',
                'translations': {'zh': {'title': '项目', 'caption': '图注'}}, 'links': [{'label': '', 'url': '', 'translations': {'zh': {'label': '论文'}}}]}],
            'currentResearch': [{'number': '01', 'title': '', 'text': '', 'status': '', 'question': '', 'method': '', 'updated': '', 'translations': {'zh': {'title': '问题'}}}],
        }
        response = client.patch('/api/v1/site/content/', payload, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        client.force_authenticate(user=None)
        result = client.get('/api/v1/site/content/').data
        self.assertEqual(result['translations']['zh']['name'], '研究者')
        self.assertEqual(result['selectedProjects'][0]['links'][0]['translations']['zh']['label'], '论文')
        self.assertEqual(result['currentResearch'][0]['translations']['zh']['title'], '问题')
        self.assertEqual(result['papersHeading'], '')
        self.assertEqual(SiteProfile.get_solo().name, '')
