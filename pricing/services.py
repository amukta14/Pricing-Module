from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple
from .models import PricingConfiguration, RideCalculation


class PricingCalculationService:
    """
    Service class for calculating ride prices using the formula:
    Price = (DBP + (Dn * DAP)) + (Tn * TMF) + WC
    
    Where:
    - DBP = Distance Base Price
    - Dn = Additional distance traveled (beyond base distance)
    - DAP = Distance Additional Price per km
    - Tn = Time component
    - TMF = Time Multiplier Factor
    - WC = Waiting Charges
    """
    
    @classmethod
    def calculate_price(
        cls,
        distance_km: float,
        time_hours: float,
        waiting_minutes: int,
        day_of_week: str,
        pricing_config_id: Optional[int] = None,
        save_calculation: bool = True,
        calculated_by: str = "API"
    ) -> Dict:
        """
        Calculate the total price for a ride based on the given parameters.
        
        Args:
            distance_km: Total distance traveled in kilometers
            time_hours: Total ride time in hours
            waiting_minutes: Total waiting time in minutes
            day_of_week: Day of the week (lowercase)
            pricing_config_id: Specific pricing configuration to use (optional)
            save_calculation: Whether to save the calculation to database
            calculated_by: Identifier for who/what performed the calculation
            
        Returns:
            Dictionary containing price breakdown and total
            
        Raises:
            ValueError: If no valid pricing configuration is found
        """
        
        # Get the appropriate pricing configuration
        pricing_config = cls._get_pricing_config(day_of_week, pricing_config_id)
        
        # Convert inputs to Decimal for precise calculations
        distance_km = Decimal(str(distance_km))
        time_hours = Decimal(str(time_hours))
        waiting_minutes = int(waiting_minutes)
        
        # Calculate each component
        dbp_component = cls._calculate_distance_base_price(distance_km, pricing_config)
        dap_component = cls._calculate_additional_distance_price(distance_km, pricing_config)
        tmf_component = cls._calculate_time_multiplier_component(time_hours, pricing_config, dbp_component + dap_component)
        wc_component = cls._calculate_waiting_charges(waiting_minutes, pricing_config)
        
        # Calculate total price using the formula
        total_price = dbp_component + dap_component + tmf_component + wc_component
        
        # Round to 2 decimal places
        total_price = total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Prepare result
        result = {
            'pricing_config_id': pricing_config.id,
            'pricing_config_name': pricing_config.name,
            'input_parameters': {
                'distance_km': float(distance_km),
                'time_hours': float(time_hours),
                'waiting_minutes': waiting_minutes,
                'day_of_week': day_of_week
            },
            'price_breakdown': {
                'distance_base_price': float(dbp_component),
                'additional_distance_price': float(dap_component),
                'time_multiplier_component': float(tmf_component),
                'waiting_charges': float(wc_component)
            },
            'total_price': float(total_price),
            'formula_applied': "DBP + DAP + TMF + WC",
            'calculation_details': {
                'base_distance_km': float(pricing_config.base_distance_km),
                'additional_distance_km': max(0, float(distance_km - pricing_config.base_distance_km)),
                'time_multiplier': cls._get_time_multiplier(time_hours, pricing_config),
                'waiting_chargeable_minutes': max(0, waiting_minutes - pricing_config.waiting_free_minutes)
            }
        }
        
        # Save calculation to database if requested
        if save_calculation:
            calculation = RideCalculation.objects.create(
                pricing_config=pricing_config,
                distance_km=distance_km,
                time_hours=time_hours,
                waiting_minutes=waiting_minutes,
                day_of_week=day_of_week,
                base_price_component=dbp_component,
                additional_distance_component=dap_component,
                time_multiplier_component=tmf_component,
                waiting_charges_component=wc_component,
                total_price=total_price,
                calculated_by=calculated_by
            )
            result['calculation_id'] = calculation.id
        
        return result
    
    @classmethod
    def _get_pricing_config(cls, day_of_week: str, pricing_config_id: Optional[int] = None) -> PricingConfiguration:
        """Get the appropriate pricing configuration"""
        if pricing_config_id:
            try:
                config = PricingConfiguration.objects.get(id=pricing_config_id, is_active=True)
                if day_of_week.lower() not in config.applicable_days:
                    raise ValueError(f"Pricing configuration {pricing_config_id} does not apply to {day_of_week}")
                return config
            except PricingConfiguration.DoesNotExist:
                raise ValueError(f"Active pricing configuration with ID {pricing_config_id} not found")
        
        # Find active configuration for the day
        configs = PricingConfiguration.objects.filter(
            is_active=True
        )
        
        # Filter by applicable days (compatible with SQLite)
        matching_configs = []
        for config in configs:
            if day_of_week.lower() in config.applicable_days:
                matching_configs.append(config)
        
        if not matching_configs:
            raise ValueError(f"No active pricing configuration found for {day_of_week}")
        
        if len(matching_configs) > 1:
            config_names = ', '.join([config.name for config in matching_configs])
            raise ValueError(
                f"Multiple active configurations found for {day_of_week}: {config_names}. "
                "Please specify pricing_config_id."
            )
        
        return matching_configs[0]
    
    @classmethod
    def _calculate_distance_base_price(cls, distance_km: Decimal, config: PricingConfiguration) -> Decimal:
        """Calculate Distance Base Price (DBP)"""
        return config.base_price
    
    @classmethod
    def _calculate_additional_distance_price(cls, distance_km: Decimal, config: PricingConfiguration) -> Decimal:
        """Calculate Additional Distance Price (Dn * DAP)"""
        additional_distance = max(Decimal('0'), distance_km - config.base_distance_km)
        return additional_distance * config.additional_price_per_km
    
    @classmethod
    def _calculate_time_multiplier_component(cls, time_hours: Decimal, config: PricingConfiguration, base_amount: Decimal) -> Decimal:
        """Calculate Time Multiplier Component (Tn * TMF)"""
        multiplier = cls._get_time_multiplier(time_hours, config)
        # Apply multiplier to the base amount (DBP + DAP)
        multiplied_amount = base_amount * Decimal(str(multiplier))
        # Return the additional amount (multiplied - original)
        return multiplied_amount - base_amount
    
    @classmethod
    def _get_time_multiplier(cls, time_hours: Decimal, config: PricingConfiguration) -> float:
        """Get the appropriate time multiplier based on ride duration"""
        time_hours_float = float(time_hours)
        
        # Sort tiers by max_hours
        tiers = sorted(config.time_multiplier_tiers, key=lambda x: x['max_hours'])
        
        # Find the appropriate tier
        for tier in tiers:
            if time_hours_float <= tier['max_hours']:
                return tier['multiplier']
        
        # If time exceeds all tiers, use the highest tier multiplier
        return tiers[-1]['multiplier'] if tiers else 1.0
    
    @classmethod
    def _calculate_waiting_charges(cls, waiting_minutes: int, config: PricingConfiguration) -> Decimal:
        """Calculate Waiting Charges (WC)"""
        return Decimal(str(config.calculate_waiting_charges(waiting_minutes)))
    
    @classmethod
    def get_active_configurations_for_day(cls, day_of_week: str) -> list:
        """Get all active pricing configurations for a specific day"""
        configs = PricingConfiguration.objects.filter(is_active=True)
        matching_configs = []
        for config in configs:
            if day_of_week.lower() in config.applicable_days:
                matching_configs.append({
                    'id': config.id,
                    'name': config.name,
                    'description': config.description
                })
        return matching_configs
    
    @classmethod
    def validate_calculation_inputs(cls, distance_km: float, time_hours: float, waiting_minutes: int, day_of_week: str) -> Dict:
        """Validate calculation inputs and return any errors"""
        errors = {}
        
        if distance_km < 0:
            errors['distance_km'] = "Distance cannot be negative"
        
        if time_hours < 0:
            errors['time_hours'] = "Time cannot be negative"
        
        if waiting_minutes < 0:
            errors['waiting_minutes'] = "Waiting minutes cannot be negative"
        
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if day_of_week.lower() not in valid_days:
            errors['day_of_week'] = f"Invalid day of week. Must be one of: {', '.join(valid_days)}"
        
        return errors 