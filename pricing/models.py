from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class PricingConfiguration(models.Model):
    """
    Model to store pricing configurations for ride services.
    Supports differential pricing based on distance, time, and day of week.
    """
    
    # Configuration metadata
    name = models.CharField(max_length=100, help_text="Name/identifier for this pricing configuration")
    description = models.TextField(blank=True, help_text="Description of this pricing configuration")
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is currently active")
    
    # Day of week configuration (stored as JSON for flexibility)
    # Format: {"monday": true, "tuesday": false, ...} or ["monday", "tuesday", ...]
    applicable_days = models.JSONField(
        help_text="Days of week this configuration applies to. JSON format: [\"monday\", \"tuesday\", ...]"
    )
    
    # Distance Base Price (DBP) configuration
    base_distance_km = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Base distance in KM (e.g., 3.0 for first 3 KM)"
    )
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Base price for the base distance (e.g., 80 INR for first 3 KM)"
    )
    
    # Distance Additional Price (DAP)
    additional_price_per_km = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per KM after base distance (e.g., 30 INR/KM)"
    )
    
    # Time Multiplier Factor (TMF) configuration
    # Stored as JSON for flexibility: [{"max_hours": 1, "multiplier": 1.0}, {"max_hours": 2, "multiplier": 1.25}, ...]
    time_multiplier_tiers = models.JSONField(
        help_text="Time multiplier tiers. JSON format: [{\"max_hours\": 1, \"multiplier\": 1.0}, {\"max_hours\": 2, \"multiplier\": 1.25}]"
    )
    
    # Waiting Charges (WC)
    waiting_free_minutes = models.IntegerField(
        default=3,
        validators=[MinValueValidator(0)],
        help_text="Free waiting time in minutes (e.g., first 3 minutes are free)"
    )
    waiting_charge_per_interval = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Charge per interval after free time (e.g., 5 INR per 3 minutes)"
    )
    waiting_interval_minutes = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Waiting charge interval in minutes (e.g., charged every 3 minutes)"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pricing_configs')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_pricing_configs')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pricing Configuration"
        verbose_name_plural = "Pricing Configurations"
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"
    
    def get_applicable_days_display(self):
        """Return human-readable format of applicable days"""
        if isinstance(self.applicable_days, list):
            return ", ".join([day.title() for day in self.applicable_days])
        return str(self.applicable_days)
    
    def calculate_time_multiplier(self, total_hours):
        """Calculate time multiplier based on total ride hours"""
        # Sort tiers by max_hours to process in order
        tiers = sorted(self.time_multiplier_tiers, key=lambda x: x['max_hours'])
        
        # Find the appropriate tier based on total hours
        for tier in tiers:
            if total_hours <= tier['max_hours']:
                return tier['multiplier']
        
        # If time exceeds all tiers, use the highest tier multiplier
        return tiers[-1]['multiplier'] if tiers else 1.0
    
    def calculate_waiting_charges(self, waiting_minutes):
        """Calculate waiting charges based on waiting time"""
        if waiting_minutes <= self.waiting_free_minutes:
            return 0
        
        chargeable_minutes = waiting_minutes - self.waiting_free_minutes
        intervals = (chargeable_minutes + self.waiting_interval_minutes - 1) // self.waiting_interval_minutes  # Ceiling division
        return intervals * self.waiting_charge_per_interval


class PricingConfigurationLog(models.Model):
    """
    Model to log all changes made to pricing configurations for audit purposes.
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('ACTIVATE', 'Activated'),
        ('DEACTIVATE', 'Deactivated'),
    ]
    
    pricing_config = models.ForeignKey(
        PricingConfiguration, 
        on_delete=models.CASCADE, 
        related_name='logs',
        null=True, 
        blank=True  # In case the config is deleted
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Store the state before and after the change
    previous_state = models.JSONField(null=True, blank=True, help_text="State before the change")
    new_state = models.JSONField(null=True, blank=True, help_text="State after the change")
    
    # Additional context/notes
    notes = models.TextField(blank=True, help_text="Additional notes about the change")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Pricing Configuration Log"
        verbose_name_plural = "Pricing Configuration Logs"
    
    def __str__(self):
        config_name = self.pricing_config.name if self.pricing_config else "Deleted Config"
        actor_name = self.actor.username if self.actor else "System"
        return f"{config_name} - {self.get_action_display()} by {actor_name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class RideCalculation(models.Model):
    """
    Model to store ride calculations for reference and debugging.
    This is optional but useful for tracking pricing calculations.
    """
    
    pricing_config = models.ForeignKey(PricingConfiguration, on_delete=models.SET_NULL, null=True)
    
    # Input parameters
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    time_hours = models.DecimalField(max_digits=10, decimal_places=2)
    waiting_minutes = models.IntegerField(default=0)
    day_of_week = models.CharField(max_length=10)
    
    # Calculated components
    base_price_component = models.DecimalField(max_digits=10, decimal_places=2)
    additional_distance_component = models.DecimalField(max_digits=10, decimal_places=2)
    time_multiplier_component = models.DecimalField(max_digits=10, decimal_places=2)
    waiting_charges_component = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Final result
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Audit
    calculated_at = models.DateTimeField(auto_now_add=True)
    calculated_by = models.CharField(max_length=100, blank=True, help_text="API user or system identifier")
    
    class Meta:
        ordering = ['-calculated_at']
        verbose_name = "Ride Calculation"
        verbose_name_plural = "Ride Calculations"
    
    def __str__(self):
        return f"Ride on {self.day_of_week} - {self.distance_km}km, {self.time_hours}h - ₹{self.total_price}"
