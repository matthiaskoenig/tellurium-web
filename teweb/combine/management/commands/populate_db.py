from django.core.management.base import BaseCommand
from teweb.combine.models import Archive

class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'populates empty database with set of OMEX archives'

    def _create_tags(self):
        tlisp = Tag(name='Lisp')
        tlisp.save()

        tjava = Tag(name='Java')
        tjava.save()

    def handle(self, *args, **options):
        self._create_archives()
