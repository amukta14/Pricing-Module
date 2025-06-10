from django import forms
from django.core.exceptions import ValidationError
from .models import PricingConfiguration
import json


class PricingConfigurationForm(forms.ModelForm):
    """
    Custom form for PricingConfiguration with enhanced validation
    """
    
    # Override applicable_days to provide better UX
    DAYS_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    applicable_days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select the days of the week this configuration applies to"
    )
    
    class Meta:
        model = PricingConfiguration
        fields = [
            'name', 'description', 'is_active', 'applicable_days',
            'base_distance_km', 'base_price', 'additional_price_per_km',
            'time_multiplier_tiers', 'waiting_free_minutes', 
            'waiting_charge_per_interval', 'waiting_interval_minutes'
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'time_multiplier_tiers': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '[{"max_hours": 1, "multiplier": 1.0}, {"max_hours": 2, "multiplier": 1.25}]'
            }),
            'base_distance_km': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'base_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'additional_price_per_km': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'waiting_charge_per_interval': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def clean_name(self):
        """Validate that the name is unique for active configurations"""
        name = self.cleaned_data.get('name')
        if name:
            # Check for existing active configurations with the same name
            existing = PricingConfiguration.objects.filter(name=name, is_active=True)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    "An active pricing configuration with this name already exists. "
                    "Please choose a different name or deactivate the existing one."
                )
        return name
    
    def clean_applicable_days(self):
        """Validate and convert applicable_days to the expected format"""
        days = self.cleaned_data.get('applicable_days')
        if not days:
            raise ValidationError("At least one day must be selected.")
        
        # Convert to lowercase list for consistency
        return [day.lower() for day in days]
    
    def clean_base_distance_km(self):
        """Validate base distance"""
        distance = self.cleaned_data.get('base_distance_km')
        if distance is not None and distance <= 0:
            raise ValidationError("Base distance must be greater than 0.")
        return distance
    
    def clean_base_price(self):
        """Validate base price"""
        price = self.cleaned_data.get('base_price')
        if price is not None and price <= 0:
            raise ValidationError("Base price must be greater than 0.")
        return price
    
    def clean_additional_price_per_km(self):
        """Validate additional price per km"""
        price = self.cleaned_data.get('additional_price_per_km')
        if price is not None and price < 0:
            raise ValidationError("Additional price per km cannot be negative.")
        return price
    
    def clean_time_multiplier_tiers(self):
        """Validate time multiplier tiers JSON format and content"""
        tiers = self.cleaned_data.get('time_multiplier_tiers')
        
        if isinstance(tiers, str):
            try:
                tiers = json.loads(tiers)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for time multiplier tiers.")
        
        if not isinstance(tiers, list):
            raise ValidationError("Time multiplier tiers must be a list.")
        
        if not tiers:
            raise ValidationError("At least one time multiplier tier must be defined.")
        
        # Validate each tier
        seen_hours = set()
        for i, tier in enumerate(tiers):
            if not isinstance(tier, dict):
                raise ValidationError(f"Tier {i+1} must be an object with 'max_hours' and 'multiplier' fields.")
            
            if 'max_hours' not in tier or 'multiplier' not in tier:
                raise ValidationError(f"Tier {i+1} must have both 'max_hours' and 'multiplier' fields.")
            
            try:
                max_hours = float(tier['max_hours'])
                multiplier = float(tier['multiplier'])
            except (ValueError, TypeError):
                raise ValidationError(f"Tier {i+1}: 'max_hours' and 'multiplier' must be numbers.")
            
            if max_hours <= 0:
                raise ValidationError(f"Tier {i+1}: 'max_hours' must be greater than 0.")
            
            if multiplier <= 0:
                raise ValidationError(f"Tier {i+1}: 'multiplier' must be greater than 0.")
            
            if max_hours in seen_hours:
                raise ValidationError(f"Tier {i+1}: Duplicate max_hours value {max_hours}.")
            
            seen_hours.add(max_hours)
        
        # Sort tiers by max_hours for consistency
        tiers.sort(key=lambda x: x['max_hours'])
        
        return tiers
    
    def clean_waiting_free_minutes(self):
        """Validate waiting free minutes"""
        minutes = self.cleaned_data.get('waiting_free_minutes')
        if minutes is not None and minutes < 0:
            raise ValidationError("Waiting free minutes cannot be negative.")
        return minutes
    
    def clean_waiting_charge_per_interval(self):
        """Validate waiting charge per interval"""
        charge = self.cleaned_data.get('waiting_charge_per_interval')
        if charge is not None and charge < 0:
            raise ValidationError("Waiting charge per interval cannot be negative.")
        return charge
    
    def clean_waiting_interval_minutes(self):
        """Validate waiting interval minutes"""
        minutes = self.cleaned_data.get('waiting_interval_minutes')
        if minutes is not None and minutes <= 0:
            raise ValidationError("Waiting interval minutes must be greater than 0.")
        return minutes
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Check if there are any conflicts with existing active configurations
        applicable_days = cleaned_data.get('applicable_days', [])
        is_active = cleaned_data.get('is_active', False)
        
        if is_active and applicable_days:
            # Check for overlapping active configurations
            all_active_configs = PricingConfiguration.objects.filter(is_active=True)
            conflicting_configs = []
            for config in all_active_configs:
                if any(day in config.applicable_days for day in applicable_days):
                    conflicting_configs.append(config)
            
            if self.instance.pk:
                conflicting_configs = [config for config in conflicting_configs if config.pk != self.instance.pk]
            
            if conflicting_configs:
                config_names = ', '.join([config.name for config in conflicting_configs[:3]])
                if len(conflicting_configs) > 3:
                    config_names += f" and {len(conflicting_configs) - 3} more"
                
                raise ValidationError(
                    f"This configuration conflicts with existing active configurations: {config_names}. "
                    "Multiple active configurations cannot apply to the same days."
                )
        
        return cleaned_data


class PriceCalculationForm(forms.Form):
    """
    Form for calculating ride prices via the API
    """
    
    DAYS_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    distance_km = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        help_text="Total distance traveled in kilometers"
    )
    
    time_hours = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        help_text="Total ride time in hours (e.g., 1.5 for 1 hour 30 minutes)"
    )
    
    waiting_minutes = forms.IntegerField(
        min_value=0,
        initial=0,
        help_text="Total waiting time in minutes"
    )
    
    day_of_week = forms.ChoiceField(
        choices=DAYS_CHOICES,
        help_text="Day of the week for the ride"
    )
    
    pricing_config_id = forms.IntegerField(
        required=False,
        help_text="Specific pricing configuration ID (optional - will use active config for the day if not provided)"
    )
    
    def clean_pricing_config_id(self):
        """Validate pricing configuration ID if provided"""
        config_id = self.cleaned_data.get('pricing_config_id')
        if config_id:
            try:
                config = PricingConfiguration.objects.get(id=config_id)
                if not config.is_active:
                    raise ValidationError("The specified pricing configuration is not active.")
                return config_id
            except PricingConfiguration.DoesNotExist:
                raise ValidationError("Pricing configuration not found.")
        return config_id
    
    def clean(self):
        """Cross-field validation for price calculation"""
        cleaned_data = super().clean()
        
        day_of_week = cleaned_data.get('day_of_week')
        pricing_config_id = cleaned_data.get('pricing_config_id')
        
        # If no specific config is provided, check if there's an active config for the day
        if not pricing_config_id and day_of_week:
            all_configs = PricingConfiguration.objects.filter(is_active=True)
            active_configs = [config for config in all_configs if day_of_week.lower() in config.applicable_days]
            
            if not active_configs:
                raise ValidationError(
                    f"No active pricing configuration found for {day_of_week.title()}. "
                    "Please specify a pricing_config_id or create an active configuration for this day."
                )
            elif len(active_configs) > 1:
                config_names = ', '.join([config.name for config in active_configs])
                raise ValidationError(
                    f"Multiple active configurations found for {day_of_week.title()}: {config_names}. "
                    "Please specify which configuration to use via pricing_config_id."
                )
        
        return cleaned_data 