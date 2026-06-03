from django.core.management.base import BaseCommand
from trip.models import TripCategory, MemberType, DocumentType, VechicleType
from finance.models import ExpensesCategory

class Command(BaseCommand):
    help = 'Seeds the database with basic static lookup values'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting database seeding..."))

        # 1. Seeding TripCategory
        categories = ["Local", "International"]
        for cat_name in categories:
            obj, created = TripCategory.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created TripCategory: '{cat_name}'"))
            else:
                self.stdout.write(f"TripCategory '{cat_name}' already exists.")

        # 2. Seeding MemberType
        member_types = ["adult", "child"]
        for mt_name in member_types:
            obj, created = MemberType.objects.get_or_create(name=mt_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created MemberType: '{mt_name}'"))
            else:
                self.stdout.write(f"MemberType '{mt_name}' already exists.")

        # 3. Seeding DocumentType
        doc_types = ["Passport", "Visa", "National ID", "Driver's License", "Travel Insurance"]
        for dt_name in doc_types:
            obj, created = DocumentType.objects.get_or_create(name=dt_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created DocumentType: '{dt_name}'"))
            else:
                self.stdout.write(f"DocumentType '{dt_name}' already exists.")

        # 4. Seeding VechicleType (matching model typo name)
        vehicle_types = ["Bus", "Car", "Train", "Flight", "Bike", "Boat"]
        for vt_name in vehicle_types:
            obj, created = VechicleType.objects.get_or_create(name=vt_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created VechicleType: '{vt_name}'"))
            else:
                self.stdout.write(f"VechicleType '{vt_name}' already exists.")

        # 5. Seeding ExpensesCategory
        expense_categories = ["Food", "Accommodation", "Transport", "Tickets & Entry Fees", "Miscellaneous"]
        for ec_name in expense_categories:
            obj, created = ExpensesCategory.objects.get_or_create(name=ec_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ExpensesCategory: '{ec_name}'"))
            else:
                self.stdout.write(f"ExpensesCategory '{ec_name}' already exists.")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
