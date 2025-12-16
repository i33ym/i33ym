from django.core.management.base import BaseCommand
from apps.rag.services.ingestion import ingest_documents


class Command(BaseCommand):
    help = "Ingest markdown documents into the RAG system"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Path to markdown files directory")
        parser.add_argument("--clear", action="store_true", help="Clear existing documents first")

    def handle(self, *args, **options):
        self.stdout.write(f"Ingesting documents from {options['path']}...")
        
        try:
            count = ingest_documents(options["path"], clear_existing=options["clear"])
            self.stdout.write(self.style.SUCCESS(f"Successfully ingested {count} chunks"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))