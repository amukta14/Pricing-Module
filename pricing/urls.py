from django.urls import path
from .views import (
    PriceCalculationAPIView,
    PricingConfigurationsAPIView,
    health_check,
    api_documentation,
    calculate_price_legacy
)

app_name = 'pricing'

urlpatterns = [
    # Main API endpoints
    path('api/calculate-price/', PriceCalculationAPIView.as_view(), name='calculate_price'),
    path('api/pricing-configurations/', PricingConfigurationsAPIView.as_view(), name='pricing_configurations'),
    
    # Utility endpoints
    path('api/health/', health_check, name='health_check'),
    path('api/docs/', api_documentation, name='api_docs'),
    
    # Legacy endpoint for backwards compatibility
    path('api/legacy/calculate-price/', calculate_price_legacy, name='calculate_price_legacy'),
] 