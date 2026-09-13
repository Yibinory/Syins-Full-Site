"""Initialize a fresh workspace without importing demo records or changing existing users."""
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.content.models import SiteProfile


class Command(BaseCommand):
    help = 'Create the first administrator and generic public profile; preserve existing installations.'

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            self.stdout.write('Existing workspace: initialization skipped.')
            return
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
        user = User(username=username, email=email)
        try:
            validate_password(password, user)
            if len(password) < 12 or password.startswith(('replace-with', 'change-this')):
                raise ValueError('Use a unique administrator password of at least 12 characters.')
            user.full_clean(exclude=['password'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        User.objects.create_superuser(username=username, email=email, password=password)
        name = os.environ.get('SITE_NAME', 'Research Space')
        SiteProfile.objects.get_or_create(pk=1, defaults={
            'name': name, 'title': 'Independent researcher', 'email': email,
            'headline': 'A space for research, ideas, and discovery.',
            'bio': 'Welcome to my research space. Explore my work and notes as this collection grows.',
            'research_directions': 'Research × Learning × Discovery',
            'current_research_heading': 'Questions in progress.',
            'featured_research_heading': 'Selected research.',
            'featured_research_intro': 'Projects and the questions behind them.',
            'publications_heading': 'Papers and publications.',
            'publications_description': 'A growing collection of published work.',
            'papers_description': 'A reading collection with recommendations, context, and linked notes.',
            'notes_heading': 'Notes and ideas.',
            'notes_description': 'A place to share what I learn.',
            'translations': {'zh': {'name': name, 'title': '独立研究者',
                'headline': '记录研究、想法与发现。', 'bio': '欢迎来到我的研究空间，这里将逐步记录我的工作与笔记。',
                'researchDirections': '研究 × 学习 × 探索', 'currentResearchHeading': '正在探索的问题。',
                'featuredResearchHeading': '精选研究。', 'featuredResearchIntro': '研究项目与背后的问题。',
                'publicationsHeading': '论文与发表成果。', 'publicationsDescription': '持续积累的研究成果。',
                'notesHeading': '笔记与想法。', 'notesDescription': '记录与分享所学。',
                'papersHeading': '推荐阅读。', 'papersDescription': '值得阅读的论文与相关笔记。',
                'toolsHeading': '工具与资源。', 'toolsDescription': '常用的研究工具与外部资源。'}},
        })
        self.stdout.write(self.style.SUCCESS('Workspace initialized without demo records.'))
