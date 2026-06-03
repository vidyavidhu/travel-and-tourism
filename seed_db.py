import os
import sys
import django
from django.core.management import call_command

def main():
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trip_Weaver.settings')
    
    # Initialize Django
    try:
        django.setup()
    except Exception as e:
        print(f"Error setting up Django environment: {e}")
        print("Please ensure you are running this script from the project root and your virtual environment is active.")
        sys.exit(1)

    print("Initializing database seed process...")
    try:
        # Call the custom seed_data management command
        call_command('seed_data')
    except Exception as e:
        print(f"Error executing seed command: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
