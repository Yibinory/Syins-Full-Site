import os
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction

from apps.content.models import CurrentResearchItem, ResearchProject, SiteProfile
from apps.core.models import Tag, WorkspaceSettings
from apps.documents.models import Document
from apps.papers.models import RecommendedPaper
from apps.publications.models import Publication
from apps.servers.models import Server


class Command(BaseCommand):
    help = "Create the first admin account and missing research workspace demo records without overwriting existing content."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "syins.yibinory@example.com")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "change-this-admin-password")
        user, created = User.objects.get_or_create(username=username, defaults={"email": email, "is_staff": True, "is_superuser": True})
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            changed = True
        if created or not user.has_usable_password():
            user.set_password(password)
            changed = True
        if changed:
            user.save()

        SiteProfile.objects.get_or_create(pk=1, defaults={
            "name": "Syins Yibinory",
            "title": "Medical imaging researcher",
            "location": "Shanghai, China",
            "email": email,
            "headline": "Learning how disease changes in images—and over time.",
            "bio": "I work at the intersection of medical image analysis and generative modeling, building systems that remain useful across hospitals, scanners, and patient timelines.",
            "research_directions": "Medical Image Processing × Domain Generalization × Image Generation",
            "featured_research_intro": "Exploring how medical images can be processed, generalized across domains, and generated.",
            "current_research_heading": "Questions I’m working on now.",
            "featured_research_heading": "Images as evidence.",
            "publications_heading": "Selected papers and preprints.",
            "publications_description": "Work on generalizable representation learning, longitudinal modeling, and controllable medical image generation.",
            "notes_heading": "Ideas in progress, organized to last.",
            "notes_description": "Research notes, essays, practical guides, and living references—kept in one public library.",
            "scholar_url": "",
            "github_url": "",
            "cv_url": "",
        })

        projects = [
            ("longitudinal", 0, "Longitudinal worlds of disease progression", "Can a generative model learn plausible futures without losing the patient in the process?", "We investigate time-aware latent representations for synthesizing anatomically consistent follow-up images from incomplete clinical histories.", "Active", "image", "/images/longitudinal-mri-mock.png", "Illustrative longitudinal MRI sequence", "Illustrative placeholder · AI-generated imagery, not experimental results", [{"label": "Project", "url": ""}, {"label": "Preprint", "url": ""}]),
            ("generalization", 1, "Generalization beyond the hospital we know", "What should a model remember when the scanner, protocol, and population all change?", "We study invariant anatomy and uncertain appearance across unseen domains in medical segmentation.", "Ongoing", "image", "/images/domain-generalization.svg", "Two source hospitals contribute to a shared model evaluated on an unseen hospital", "Conceptual illustration · Cross-hospital generalization", [{"label": "Paper", "url": ""}, {"label": "Code", "url": ""}]),
        ]
        for key, order, title, motivation, approach, project_status, media_type, media_url, media_alt, caption, links in projects:
            project_id = uuid.uuid5(uuid.NAMESPACE_URL, "https://research-os.local/project/" + key)
            ResearchProject.objects.get_or_create(id=project_id, defaults={"order": order, "title": title, "motivation": motivation, "approach": approach, "status": project_status, "media_type": media_type, "media_url": media_url, "media_alt": media_alt, "caption": caption, "links": links})

        current = [
            ("01", 0, "Medical Image Generation", "Controllable generative models that preserve anatomy while exposing clinically meaningful variation.", "Active", "How can pathology change without silently changing patient identity?", "Anatomy-conditioned diffusion · Counterfactual editing", "Updated 2 days ago"),
            ("02", 1, "Longitudinal Image Modeling", "Learning patient-specific trajectories to model disease progression across sparse clinical timepoints.", "Exploring", "What does a plausible future image look like when observations are sparse and irregular?", "Temporal latent models · Calibrated uncertainty", "Updated today"),
            ("03", 2, "Domain Generalization", "Robust representations that transfer across scanners, institutions, and unseen acquisition protocols.", "Active", "Which visual features survive a change of hospital, scanner, and population?", "Invariant representation learning · OOD evaluation", "Updated 5 days ago"),
        ]
        for number, order, title, text, item_status, question, method, updated in current:
            CurrentResearchItem.objects.get_or_create(number=number, defaults={"order": order, "title": title, "text": text, "status": item_status, "question": question, "method": method, "updated_label": updated, "enabled": True})

        publication_data = [
            ("anatomy-preserving-generative-priors", "Anatomy-Preserving Generative Priors for Cross-Domain Medical Segmentation", "Syins Yibinory, Yiming Chen, Ming Li", "European Conference on Computer Vision", "ECCV", 2026, "Conference", "Anatomy-preserving priors for robust segmentation under acquisition shifts.", "A generative prior separates anatomical structure from scanner-specific appearance.", "", True, "/images/longitudinal-mri-mock.png", ["Domain Generalization", "Segmentation"]),
            ("temporal-anatomy-longitudinal-synthesis", "Temporal Anatomy as a Prior for Longitudinal MR Image Synthesis", "Syins Yibinory, Jiawen Wu, Rui Zhang", "Medical Image Computing and Computer Assisted Intervention", "MICCAI", 2025, "Conference", "Can a generative model learn plausible futures without losing the patient in the process?", "A time-aware latent representation conditions synthesis on sparse patient histories.", "", True, "", ["Generation", "Longitudinal MRI"]),
            ("uncertainty-aware-harmonization", "Uncertainty-aware Harmonization under Unseen Acquisition Shifts", "Syins Yibinory, Lin Zhou, Ming Li", "IEEE Transactions on Medical Imaging", "TMI", 2025, "Journal", "", "", "", False, "", ["Harmonization", "Uncertainty"]),
            ("counterfactual-pathology-editing", "Counterfactual Pathology Editing with Spatially Grounded Diffusion", "Syins Yibinory, Yiming Chen", "arXiv preprint", "arXiv", 2024, "Preprint", "", "", "", False, "", ["Diffusion", "Counterfactual"]),
        ]
        for slug, title, authors, venue, venue_short, year, publication_type, motivation, approach, abstract, featured, media_url, tags in publication_data:
            publication, created = Publication.objects.get_or_create(slug=slug, defaults={"title": title, "authors": authors, "venue": venue, "venue_short": venue_short, "year": year, "type": publication_type, "motivation": motivation, "approach": approach, "abstract": abstract, "featured": featured, "media_url": media_url, "media_type": "image"})
            if created:
                self.set_tags(publication, tags)

        notes = [
            ("towards-longitudinal-medical-image-generation", "Towards Longitudinal Medical Image Generation", "Research notes on temporal consistency, uncertainty, and disease progression.", "A living research note on what it means to generate a plausible future scan: preserve patient identity, represent uncertainty, and make change clinically legible.", "Research Note", "2026-09-10", "public", True, ["Longitudinal", "Generation", "MRI"], "# Towards Longitudinal Medical Image Generation\n\nA working note on temporal consistency, uncertainty, and disease progression."),
            ("evaluating-domain-generalization", "Evaluating Domain Generalization Without Fooling Ourselves", "A practical argument for stronger splits, honest baselines, and uncertainty-aware reporting.", "Generalization claims are only as useful as the unseen domains used to test them.", "Essay", "2026-08-24", "public", False, ["Domain Generalization", "Evaluation"], "# Evaluating Domain Generalization Without Fooling Ourselves\n\nGeneralization claims are only as useful as the unseen domains used to test them."),
            ("reproducible-monai-experiments", "A Reproducible MONAI Experiment Setup", "Project layout, configuration boundaries, deterministic training, and experiment metadata.", "A maintained setup guide for turning a promising notebook into a repeatable medical imaging experiment.", "Guide", "2026-08-02", "public", False, ["MONAI", "PyTorch", "Reproducibility"], "# A Reproducible MONAI Experiment Setup\n\nA maintained setup guide for repeatable medical imaging experiments."),
            ("medical-image-generation-reading-map", "Medical Image Generation — A Reading Map", "A structured index of diffusion, flow matching, evaluation, and clinical translation papers.", "Not a static bibliography, but a map organized around the questions each line of work is trying to answer.", "Reference", "2026-07-18", "public", False, ["Reading List", "Diffusion", "Evaluation"], "# Medical Image Generation — A Reading Map\n\nA living reading map."),
            ("temporal-consistency-metrics", "Notes on Temporal Consistency Metrics", "What pixel, perceptual, anatomical, and clinical measures each fail to capture.", "A short comparison of metrics for evaluating generated longitudinal sequences.", "Research Note", "2026-06-29", "public", False, ["Metrics", "Temporal Modeling"], "# Notes on Temporal Consistency Metrics\n\nA short comparison of metrics."),
        ]
        for slug, title, summary, excerpt, kind, published_at, visibility, featured, tags, content in notes:
            note, created = Document.objects.get_or_create(slug=slug, defaults={"title": title, "summary": summary, "excerpt": excerpt, "kind": kind, "published_at": date.fromisoformat(published_at), "visibility": visibility, "featured": featured, "content": content, "reading_time": "8 min"})
            if created:
                self.set_tags(note, tags)

        paper_data = [
            (31, "MedMamba: Vision Mamba for Medical Image Classification", "Yue et al.", "arXiv", 2026, "Medical Image Analysis", "read", "Sep 08, 2026", "Useful backbone comparison for representation experiments.", "A selective state-space architecture adapted to multi-scale medical image classification.", 4, "", "2403.03849", ["Mamba", "Classification"]),
            (30, "Temporal Diffusion for Longitudinal Medical Image Synthesis", "Chen, Wang, Li et al.", "MICCAI", 2026, "Medical Image Generation", "important", "Sep 07, 2026", "Directly overlaps with temporal consistency and sparse visits.", "A diffusion formulation for synthesizing future scans conditioned on irregular patient timelines.", 5, "10.1007/example.2026.31", "", ["Diffusion", "Longitudinal", "MRI"]),
            (29, "Do Domain Generalization Methods Generalize Well?", "Gulrajani & Lopez-Paz", "ICLR", 2021, "Domain Generalization", "reading", "Sep 04, 2026", "Foundational benchmark methodology for evaluating DG claims.", "A controlled study of domain generalization algorithms under consistent model selection.", None, "", "", ["Benchmark", "OOD"]),
            (28, "Latent Disease Trajectories from Sparse Clinical Imaging", "Park et al.", "TMI", 2025, "Disease Progression", "to_read", "Aug 29, 2026", "Connects time-to-event modeling with imaging representations.", "Latent variable models align irregular clinical observations into disease progression trajectories.", None, "", "", ["Trajectory", "CT", "Survival"]),
            (27, "Segment Anything in Medical Images", "Ma et al.", "Nature Communications", 2024, "Medical Image Analysis", "read", "Aug 18, 2026", "Relevant foundation model baseline.", "A promptable segmentation foundation model adapted across medical imaging modalities.", 4, "", "", ["Foundation Model", "Segmentation"]),
        ]
        for paper_id, title, authors, venue, year, topic, paper_status, recommended_at, reason, abstract, rating, doi, arxiv_id, tags in paper_data:
            paper, created = RecommendedPaper.objects.get_or_create(id=paper_id, defaults={"title": title, "authors": authors, "venue": venue, "year": year, "topic": topic, "status": paper_status, "recommended_at": date.fromisoformat(self.parse_paper_date(recommended_at)), "reason": reason, "abstract": abstract, "rating": rating, "doi": doi, "arxiv_id": arxiv_id, "paper_url": "https://arxiv.org/abs/{}".format(arxiv_id) if arxiv_id else "", "publicly_visible": True})
            if created:
                self.set_tags(paper, tags)

        servers = [
            (1, "GPU8-Lab", "gpu8.lab.local", "10.10.0.18", "Primary training workstation", "Lab · Rack A", "Ubuntu 24.04", "online", ["SSH", "Docker", "NVIDIA_GPU", "Monitoring"], 37, {"used": 142, "total": 256}, {"used": 2.1, "total": 4}, [{"name": "RTX 4090", "utilization": 92, "memory": "21.4 / 24 GB", "temperature": 71}, {"name": "RTX 4090", "utilization": 81, "memory": "19.2 / 24 GB", "temperature": 68}, {"name": "RTX 4090", "utilization": 97, "memory": "22.8 / 24 GB", "temperature": 74}, {"name": "RTX 4090", "utilization": 63, "memory": "14.1 / 24 GB", "temperature": 61}], 12),
            (2, "Archive-NAS", "archive.home", "10.10.0.7", "Datasets and experiment archives", "Home", "Debian 13", "online", ["SSH", "Docker", "Monitoring"], 12, {"used": 18, "total": 64}, {"used": 31.2, "total": 48}, [], 5),
            (3, "Edge-SG", "edge-sg.internal", "10.22.1.4", "Remote services and 3x-ui", "Singapore", "Ubuntu 22.04", "warning", ["SSH", "Docker", "XUI", "Monitoring"], 68, {"used": 7.2, "total": 8}, {"used": 78, "total": 120}, [], 8),
            (4, "Old-Workstation", "ws03.lab.local", "10.10.0.23", "Legacy analysis node", "Lab · Desk 3", "Ubuntu 20.04", "offline", ["SSH", "NVIDIA_GPU"], 0, {"used": 0, "total": 64}, {"used": 1.4, "total": 2}, [{"name": "RTX 3090", "utilization": 0, "memory": "—", "temperature": 0}], 0),
        ]
        for server_id, name, hostname, ip, description, location, os_name, server_status, capabilities, cpu, memory, disk, gpus, containers in servers:
            Server.objects.get_or_create(id=server_id, defaults={"name": name, "hostname": hostname, "ip": ip, "description": description, "location": location, "os": os_name, "status": server_status, "provider": "mock", "is_primary": server_id == 1, "uptime": "—" if server_status == "offline" else "38 days", "capabilities": capabilities, "cpu": cpu, "memory": memory, "disk": disk, "gpus": gpus, "containers": containers, "enabled": True})

        # Several legacy demo records keep their visible numeric ids. Reset the
        # database sequences so the next user-created record cannot collide.
        with connection.cursor() as cursor:
            for sql in connection.ops.sequence_reset_sql(no_style(), [RecommendedPaper, Server]):
                cursor.execute(sql)

        WorkspaceSettings.get_solo()
        self.stdout.write(self.style.SUCCESS("Research OS demo data is ready."))
        self.stdout.write("Admin username: {}".format(username))
        if password == "change-this-admin-password":
            self.stdout.write(self.style.WARNING("Change DJANGO_SUPERUSER_PASSWORD before production deployment."))

    @staticmethod
    def set_tags(instance, names):
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        instance.tags.set(tags)

    @staticmethod
    def parse_paper_date(value):
        return date.fromisoformat("{}-{}-{}".format(value[-4:], {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}[value[:3]], value[4:6].replace(",", "").strip())).isoformat()
