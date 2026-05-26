from django.db import migrations

def seed_categories(apps, schema_editor):
    ExpensesCategory = apps.get_model('finance', 'ExpensesCategory')
    categories = [
        'Petrol',
        'Hotel Bill',
        'Restaurant Bill',
        'Vehicle Rent',
        'Guide',
        'Medical',
        'Tickets',
        'Toll',
        'Fine',
        'Other'
    ]
    for category in categories:
        ExpensesCategory.objects.get_or_create(name=category)

def reverse_seed_categories(apps, schema_editor):
    ExpensesCategory = apps.get_model('finance', 'ExpensesCategory')
    ExpensesCategory.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=reverse_seed_categories),
    ]
