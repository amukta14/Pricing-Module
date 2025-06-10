from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .services import PricingCalculationService
from .forms import PriceCalculationForm
from .models import PricingConfiguration


class PriceCalculationAPIView(APIView):
    """
    API endpoint for calculating ride prices.
    
    POST /api/calculate-price/
    
    Request Body:
    {
        "distance_km": 5.5,
        "time_hours": 1.5,
        "waiting_minutes": 10,
        "day_of_week": "monday",
        "pricing_config_id": 1  // optional
    }
    
    Response:
    {
        "success": true,
        "data": {
            "pricing_config_id": 1,
            "pricing_config_name": "Weekday Standard",
            "input_parameters": {
                "distance_km": 5.5,
                "time_hours": 1.5,
                "waiting_minutes": 10,
                "day_of_week": "monday"
            },
            "price_breakdown": {
                "distance_base_price": 80.0,
                "additional_distance_price": 75.0,
                "time_multiplier_component": 38.75,
                "waiting_charges": 10.0
            },
            "total_price": 203.75,
            "formula_applied": "DBP + DAP + TMF + WC",
            "calculation_details": {
                "base_distance_km": 3.0,
                "additional_distance_km": 2.5,
                "time_multiplier": 1.25,
                "waiting_chargeable_minutes": 7
            },
            "calculation_id": 123
        }
    }
    """
    
    def post(self, request):
        """Calculate price for a ride"""
        try:
            # Parse request data
            data = request.data
            
            # Validate required fields
            required_fields = ['distance_km', 'time_hours', 'waiting_minutes', 'day_of_week']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return Response({
                    'success': False,
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract parameters
            distance_km = float(data['distance_km'])
            time_hours = float(data['time_hours'])
            waiting_minutes = int(data['waiting_minutes'])
            day_of_week = str(data['day_of_week']).lower()
            pricing_config_id = data.get('pricing_config_id')
            
            # Validate inputs
            validation_errors = PricingCalculationService.validate_calculation_inputs(
                distance_km, time_hours, waiting_minutes, day_of_week
            )
            
            if validation_errors:
                return Response({
                    'success': False,
                    'error': 'Validation failed',
                    'validation_errors': validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate price
            try:
                result = PricingCalculationService.calculate_price(
                    distance_km=distance_km,
                    time_hours=time_hours,
                    waiting_minutes=waiting_minutes,
                    day_of_week=day_of_week,
                    pricing_config_id=pricing_config_id,
                    calculated_by=f"API:{request.META.get('REMOTE_ADDR', 'unknown')}"
                )
                
                return Response({
                    'success': True,
                    'data': result
                }, status=status.HTTP_200_OK)
                
            except ValueError as e:
                return Response({
                    'success': False,
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except (ValueError, TypeError, KeyError) as e:
            return Response({
                'success': False,
                'error': f'Invalid request data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PricingConfigurationsAPIView(APIView):
    """
    API endpoint to get available pricing configurations.
    
    GET /api/pricing-configurations/
    GET /api/pricing-configurations/?day_of_week=monday
    """
    
    def get(self, request):
        """Get list of active pricing configurations, optionally filtered by day"""
        try:
            day_of_week = request.GET.get('day_of_week')
            
            if day_of_week:
                day_of_week = day_of_week.lower()
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if day_of_week not in valid_days:
                    return Response({
                        'success': False,
                        'error': f'Invalid day_of_week. Must be one of: {", ".join(valid_days)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                all_configs = PricingConfiguration.objects.filter(is_active=True)
                configs = [config for config in all_configs if day_of_week in config.applicable_days]
            else:
                configs = PricingConfiguration.objects.filter(is_active=True)
            
            config_data = []
            for config in configs:
                config_data.append({
                    'id': config.id,
                    'name': config.name,
                    'description': config.description,
                    'applicable_days': config.applicable_days,
                    'base_distance_km': float(config.base_distance_km),
                    'base_price': float(config.base_price),
                    'additional_price_per_km': float(config.additional_price_per_km),
                    'time_multiplier_tiers': config.time_multiplier_tiers,
                    'waiting_free_minutes': config.waiting_free_minutes,
                    'waiting_charge_per_interval': float(config.waiting_charge_per_interval),
                    'waiting_interval_minutes': config.waiting_interval_minutes
                })
            
            return Response({
                'success': True,
                'data': {
                    'configurations': config_data,
                    'count': len(config_data),
                    'filtered_by_day': day_of_week
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint.
    
    GET /api/health/
    """
    return Response({
        'status': 'healthy',
        'service': 'pricing-module',
        'version': '1.0.0'
    })


@api_view(['GET'])
def api_documentation(request):
    """
    API documentation endpoint.
    
    GET /api/docs/
    """
    docs = {
        'title': 'Pricing Module API',
        'version': '1.0.0',
        'description': 'API for calculating ride prices based on configurable pricing models',
        'endpoints': [
            {
                'path': '/api/calculate-price/',
                'method': 'POST',
                'description': 'Calculate price for a ride',
                'parameters': {
                    'distance_km': 'float - Total distance traveled in kilometers',
                    'time_hours': 'float - Total ride time in hours',
                    'waiting_minutes': 'int - Total waiting time in minutes',
                    'day_of_week': 'string - Day of the week (monday, tuesday, etc.)',
                    'pricing_config_id': 'int - Optional specific pricing configuration ID'
                },
                'example_request': {
                    'distance_km': 5.5,
                    'time_hours': 1.5,
                    'waiting_minutes': 10,
                    'day_of_week': 'monday'
                }
            },
            {
                'path': '/api/pricing-configurations/',
                'method': 'GET',
                'description': 'Get list of active pricing configurations',
                'parameters': {
                    'day_of_week': 'string - Optional filter by day of week'
                }
            },
            {
                'path': '/api/health/',
                'method': 'GET',
                'description': 'Health check endpoint'
            }
        ],
        'formula': 'Price = (DBP + (Dn * DAP)) + (Tn * TMF) + WC',
        'formula_explanation': {
            'DBP': 'Distance Base Price',
            'Dn': 'Additional distance traveled (beyond base distance)',
            'DAP': 'Distance Additional Price per km',
            'Tn': 'Time component',
            'TMF': 'Time Multiplier Factor',
            'WC': 'Waiting Charges'
        }
    }
    
    return Response(docs)


# Legacy function-based view for backwards compatibility
@csrf_exempt
def calculate_price_legacy(request):
    """
    Legacy function-based view for price calculation.
    Maintained for backwards compatibility.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    
    # Use the same logic as the class-based view
    view = PriceCalculationAPIView()
    view.request = request
    response = view.post(request)
    
    return JsonResponse(response.data, status=response.status_code)
