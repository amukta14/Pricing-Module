from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from .models import PricingConfiguration, PricingConfigurationLog, RideCalculation
import json
from django.core.serializers.json import DjangoJSONEncoder


@admin.register(PricingConfiguration)
class PricingConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'base_price', 'additional_price_per_km', 'get_applicable_days_display', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at', 'applicable_days']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active', 'applicable_days')
        }),
        ('Distance Pricing', {
            'fields': ('base_distance_km', 'base_price', 'additional_price_per_km')
        }),
        ('Time Multiplier Configuration', {
            'fields': ('time_multiplier_tiers',),
            'description': 'Configure time-based multipliers. Format: [{"max_hours": 1, "multiplier": 1.0}, {"max_hours": 2, "multiplier": 1.25}]'
        }),
        ('Waiting Charges', {
            'fields': ('waiting_free_minutes', 'waiting_charge_per_interval', 'waiting_interval_minutes')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Override save to log changes and set audit fields"""
        # Capture previous state for logging
        previous_state = None
        action = 'CREATE'
        
        if change and obj.pk:
            try:
                previous_obj = PricingConfiguration.objects.get(pk=obj.pk)
                previous_state = self._model_to_dict(previous_obj)
                action = 'UPDATE'
            except PricingConfiguration.DoesNotExist:
                pass
        
        # Set audit fields
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Save the object
        super().save_model(request, obj, form, change)
        
        # Log the change
        new_state = self._model_to_dict(obj)
        PricingConfigurationLog.objects.create(
            pricing_config=obj,
            action=action,
            actor=request.user,
            previous_state=previous_state,
            new_state=new_state,
            notes=f"Modified via Django Admin"
        )
    
    def delete_model(self, request, obj):
        """Override delete to log the action"""
        previous_state = self._model_to_dict(obj)
        
        # Log the deletion
        PricingConfigurationLog.objects.create(
            pricing_config=None,  # Will be null after deletion
            action='DELETE',
            actor=request.user,
            previous_state=previous_state,
            new_state=None,
            notes=f"Deleted '{obj.name}' via Django Admin"
        )
        
        super().delete_model(request, obj)
    
    def _model_to_dict(self, obj):
        """Convert model instance to dictionary for logging"""
        return {
            'name': obj.name,
            'description': obj.description,
            'is_active': obj.is_active,
            'applicable_days': obj.applicable_days,
            'base_distance_km': float(obj.base_distance_km),
            'base_price': float(obj.base_price),
            'additional_price_per_km': float(obj.additional_price_per_km),
            'time_multiplier_tiers': obj.time_multiplier_tiers,
            'waiting_free_minutes': obj.waiting_free_minutes,
            'waiting_charge_per_interval': float(obj.waiting_charge_per_interval),
            'waiting_interval_minutes': obj.waiting_interval_minutes,
        }
    
    actions = ['activate_configurations', 'deactivate_configurations']
    
    def activate_configurations(self, request, queryset):
        """Custom action to activate multiple configurations"""
        for obj in queryset:
            if not obj.is_active:
                previous_state = self._model_to_dict(obj)
                obj.is_active = True
                obj.updated_by = request.user
                obj.save()
                
                new_state = self._model_to_dict(obj)
                PricingConfigurationLog.objects.create(
                    pricing_config=obj,
                    action='ACTIVATE',
                    actor=request.user,
                    previous_state=previous_state,
                    new_state=new_state,
                    notes="Activated via bulk action in Django Admin"
                )
        
        self.message_user(request, f"Successfully activated {queryset.count()} configurations.")
    activate_configurations.short_description = "Activate selected configurations"
    
    def deactivate_configurations(self, request, queryset):
        """Custom action to deactivate multiple configurations"""
        for obj in queryset:
            if obj.is_active:
                previous_state = self._model_to_dict(obj)
                obj.is_active = False
                obj.updated_by = request.user
                obj.save()
                
                new_state = self._model_to_dict(obj)
                PricingConfigurationLog.objects.create(
                    pricing_config=obj,
                    action='DEACTIVATE',
                    actor=request.user,
                    previous_state=previous_state,
                    new_state=new_state,
                    notes="Deactivated via bulk action in Django Admin"
                )
        
        self.message_user(request, f"Successfully deactivated {queryset.count()} configurations.")
    deactivate_configurations.short_description = "Deactivate selected configurations"


@admin.register(PricingConfigurationLog)
class PricingConfigurationLogAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'action', 'actor', 'timestamp', 'pricing_config']
    list_filter = ['action', 'timestamp', 'actor']
    search_fields = ['pricing_config__name', 'actor__username', 'notes']
    readonly_fields = ['pricing_config', 'action', 'actor', 'timestamp', 'previous_state', 'new_state', 'notes']
    
    def has_add_permission(self, request):
        """Prevent manual creation of log entries"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of log entries"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of log entries"""
        return False
    
    fieldsets = (
        ('Log Information', {
            'fields': ('pricing_config', 'action', 'actor', 'timestamp', 'notes')
        }),
        ('State Changes', {
            'fields': ('previous_state', 'new_state'),
            'classes': ('collapse',),
            'description': 'JSON representation of the object state before and after the change'
        })
    )


@admin.register(RideCalculation)
class RideCalculationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'pricing_config', 'distance_km', 'time_hours', 'waiting_minutes', 'total_price', 'calculated_at']
    list_filter = ['day_of_week', 'calculated_at', 'pricing_config']
    search_fields = ['pricing_config__name', 'calculated_by']
    readonly_fields = ['calculated_at']
    
    fieldsets = (
        ('Input Parameters', {
            'fields': ('pricing_config', 'distance_km', 'time_hours', 'waiting_minutes', 'day_of_week')
        }),
        ('Price Breakdown', {
            'fields': ('base_price_component', 'additional_distance_component', 'time_multiplier_component', 'waiting_charges_component', 'total_price')
        }),
        ('Audit', {
            'fields': ('calculated_at', 'calculated_by')
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly for existing objects to preserve calculation integrity"""
        if obj:  # Editing an existing object
            return [field.name for field in self.model._meta.fields]
        return self.readonly_fields


# Customize the admin site header and title
admin.site.site_header = "Pricing Module Administration"
admin.site.site_title = "Pricing Module"
admin.site.index_title = "Welcome to Pricing Module Administration"
