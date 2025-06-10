#!/usr/bin/env python
"""
Script to create sample pricing configurations for demonstration.
Run this after setting up the database.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pricing_module.settings')
django.setup()

from django.contrib.auth.models import User
from pricing.models import PricingConfiguration
from decimal import Decimal

def create_sample_data():
    """Create sample pricing configurations"""
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_superuser': True,
            'is_staff': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✅ Created admin user")
    
    # Sample Configuration 1: Standard Weekday
    weekday_config, created = PricingConfiguration.objects.get_or_create(
        name="Standard Weekday",
        defaults={
            'description': "Standard pricing for Monday to Friday",
            'is_active': True,
            'applicable_days': ["monday", "tuesday", "wednesday", "thursday", "friday"],
            'base_distance_km': Decimal('3.0'),
            'base_price': Decimal('80.0'),
            'additional_price_per_km': Decimal('30.0'),
            'time_multiplier_tiers': [
                {"max_hours": 1, "multiplier": 1.0},
                {"max_hours": 2, "multiplier": 1.25},
                {"max_hours": 3, "multiplier": 1.5}
            ],
            'waiting_free_minutes': 3,
            'waiting_charge_per_interval': Decimal('5.0'),
            'waiting_interval_minutes': 3,
            'created_by': admin_user,
            'updated_by': admin_user
        }
    )
    if created:
        print("✅ Created Standard Weekday configuration")
    
    # Sample Configuration 2: Weekend Premium
    weekend_config, created = PricingConfiguration.objects.get_or_create(
        name="Weekend Premium",
        defaults={
            'description': "Premium pricing for weekends with higher rates",
            'is_active': True,
            'applicable_days': ["saturday", "sunday"],
            'base_distance_km': Decimal('3.5'),
            'base_price': Decimal('95.0'),
            'additional_price_per_km': Decimal('35.0'),
            'time_multiplier_tiers': [
                {"max_hours": 1, "multiplier": 1.2},
                {"max_hours": 2, "multiplier": 1.5},
                {"max_hours": 3, "multiplier": 2.0}
            ],
            'waiting_free_minutes': 3,
            'waiting_charge_per_interval': Decimal('7.0'),
            'waiting_interval_minutes': 3,
            'created_by': admin_user,
            'updated_by': admin_user
        }
    )
    if created:
        print("✅ Created Weekend Premium configuration")
    
    # Sample Configuration 3: Night Time (Inactive example)
    night_config, created = PricingConfiguration.objects.get_or_create(
        name="Night Time Special",
        defaults={
            'description': "Special pricing for late night rides (currently inactive)",
            'is_active': False,  # Inactive to show management
            'applicable_days': ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            'base_distance_km': Decimal('2.5'),
            'base_price': Decimal('100.0'),
            'additional_price_per_km': Decimal('40.0'),
            'time_multiplier_tiers': [
                {"max_hours": 1, "multiplier": 1.5},
                {"max_hours": 2, "multiplier": 2.0}
            ],
            'waiting_free_minutes': 2,
            'waiting_charge_per_interval': Decimal('8.0'),
            'waiting_interval_minutes': 2,
            'created_by': admin_user,
            'updated_by': admin_user
        }
    )
    if created:
        print("✅ Created Night Time Special configuration (inactive)")
    
    print("\n🎉 Sample data created successfully!")
    print("\nYou can now:")
    print("1. View configurations in Django Admin: http://127.0.0.1:8000/admin/")
    print("2. Test the API with these sample configurations")
    print("3. Modify configurations to see audit logging in action")

if __name__ == "__main__":
    create_sample_data() 