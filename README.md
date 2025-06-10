# Pricing Module

A comprehensive Django web application with a configurable pricing module that supports differential pricing for ride services. This application implements a flexible pricing system similar to ride-sharing services like Uber/Ola.

## Features

- **Configurable Pricing**: Store and manage multiple pricing configurations
- **Differential Pricing**: Support for different prices based on:
  - Day of the week
  - Distance traveled (base + additional)
  - Time duration with multiplier tiers
  - Waiting time charges
- **Django Admin Interface**: User-friendly interface for managing pricing configurations
- **REST API**: Calculate pricing dynamically via API endpoints
- **Audit Logging**: Complete change tracking with actor and timestamp
- **Comprehensive Validation**: Form and API validation for all pricing parameters
- **Test Coverage**: Extensive test suite for models, services, and APIs

## Formula

The pricing calculation follows this formula:

```
Price = (DBP + (Dn × DAP)) + (Tn × TMF) + WC
```

Where:
- **DBP**: Distance Base Price (fixed price for base distance)
- **Dn**: Additional distance traveled (beyond base distance)
- **DAP**: Distance Additional Price per km
- **Tn**: Time component 
- **TMF**: Time Multiplier Factor (based on ride duration)
- **WC**: Waiting Charges

## Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository** (or extract the provided files)
   ```bash
   cd pricing_module
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv pricing_env
   source pricing_env/bin/activate  # On Windows: pricing_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser for admin access**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

The application will be available at:
- **Admin Interface**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/docs/
- **Health Check**: http://127.0.0.1:8000/api/health/

### Default Admin Credentials

If you used the setup script, the default admin credentials are:
- **Username**: `admin`
- **Password**: `admin123`

## API Endpoints

### 1. Calculate Price

**POST** `/api/calculate-price/`

Calculate ride price based on input parameters.

#### Request Body
```json
{
    "distance_km": 5.5,
    "time_hours": 1.5,
    "waiting_minutes": 10,
    "day_of_week": "monday",
    "pricing_config_id": 1  // optional
}
```

#### Response
```json
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
```

### 2. Get Pricing Configurations

**GET** `/api/pricing-configurations/`

Get list of active pricing configurations, optionally filtered by day.

#### Query Parameters
- `day_of_week`: Filter by specific day (monday, tuesday, etc.)

#### Response
```json
{
    "success": true,
    "data": {
        "configurations": [
            {
                "id": 1,
                "name": "Weekday Standard",
                "description": "Standard pricing for weekdays",
                "applicable_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "base_distance_km": 3.0,
                "base_price": 80.0,
                "additional_price_per_km": 30.0,
                "time_multiplier_tiers": [
                    {"max_hours": 1, "multiplier": 1.0},
                    {"max_hours": 2, "multiplier": 1.25}
                ],
                "waiting_free_minutes": 3,
                "waiting_charge_per_interval": 5.0,
                "waiting_interval_minutes": 3
            }
        ],
        "count": 1,
        "filtered_by_day": null
    }
}
```

### 3. Health Check

**GET** `/api/health/`

Simple health check endpoint.

### 4. API Documentation

**GET** `/api/docs/`

Get complete API documentation.

## Django Admin Interface

The Django Admin provides a user-friendly interface for managing pricing configurations:

### Pricing Configurations
- **Create/Edit/Delete** pricing configurations
- **Activate/Deactivate** configurations
- **Bulk Actions** for managing multiple configurations
- **Automatic Validation** of configuration parameters
- **Conflict Detection** for overlapping active configurations

### Configuration Log
- **View-only** audit trail of all changes
- **Actor Tracking** (who made the change)
- **State Changes** (before and after values)
- **Timestamps** for all modifications

### Ride Calculations
- **View** historical price calculations
- **Filter** by configuration, date, or day of week
- **Analyze** pricing patterns and usage

## Configuration Examples

### Basic Weekday Configuration
```json
{
    "name": "Standard Weekday",
    "description": "Basic pricing for Monday-Friday",
    "applicable_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "base_distance_km": 3.0,
    "base_price": 80.0,
    "additional_price_per_km": 30.0,
    "time_multiplier_tiers": [
        {"max_hours": 1, "multiplier": 1.0},
        {"max_hours": 2, "multiplier": 1.25},
        {"max_hours": 3, "multiplier": 1.5}
    ],
    "waiting_free_minutes": 3,
    "waiting_charge_per_interval": 5.0,
    "waiting_interval_minutes": 3
}
```

### Weekend Premium Configuration
```json
{
    "name": "Weekend Premium",
    "description": "Higher pricing for weekends",
    "applicable_days": ["saturday", "sunday"],
    "base_distance_km": 3.5,
    "base_price": 95.0,
    "additional_price_per_km": 35.0,
    "time_multiplier_tiers": [
        {"max_hours": 1, "multiplier": 1.2},
        {"max_hours": 2, "multiplier": 1.5}
    ],
    "waiting_free_minutes": 3,
    "waiting_charge_per_interval": 7.0,
    "waiting_interval_minutes": 3
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python manage.py test

# Run specific test classes
python manage.py test pricing.tests.PricingCalculationServiceTest
python manage.py test pricing.tests.PricingAPITest

# Run with verbose output
python manage.py test --verbosity=2
```

### Test Coverage

The test suite covers:
- **Model functionality** and validation
- **Service layer** pricing calculations
- **API endpoints** and error handling
- **Form validation** and business rules
- **Admin interface** logging functionality

## Architecture

### Models
- `PricingConfiguration`: Store pricing rules and parameters
- `PricingConfigurationLog`: Audit trail for configuration changes
- `RideCalculation`: Historical record of price calculations

### Services
- `PricingCalculationService`: Core pricing logic and formula implementation

### Views
- `PriceCalculationAPIView`: Main API for price calculation
- `PricingConfigurationsAPIView`: Configuration management API

### Forms
- `PricingConfigurationForm`: Admin form with validation
- `PriceCalculationForm`: API input validation

## Development

### Project Structure
```
pricing_module/
├── pricing/                 # Main application
│   ├── models.py           # Database models
│   ├── services.py         # Business logic
│   ├── views.py            # API views
│   ├── forms.py            # Django forms
│   ├── admin.py            # Admin configuration
│   ├── tests.py            # Test suite
│   └── urls.py             # URL routing
├── pricing_module/         # Project configuration
│   ├── settings.py         # Django settings
│   └── urls.py             # Main URL routing
├── manage.py               # Django management
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Adding New Features

1. **New Pricing Parameters**: Extend the `PricingConfiguration` model
2. **Custom Calculations**: Modify `PricingCalculationService`
3. **API Endpoints**: Add new views and URL patterns
4. **Validation Rules**: Update forms and service validation

## Troubleshooting

### Common Issues

1. **Migration Errors**
   ```bash
   python manage.py makemigrations --empty pricing
   python manage.py migrate
   ```

2. **Admin Access Issues**
   ```bash
   python manage.py createsuperuser
   ```

3. **API 500 Errors**: Check logs and ensure database is migrated

### Logs and Debugging

- Enable Django debug mode in `settings.py`
- Check database tables are created: `python manage.py dbshell`
- Use Django's built-in logging for debugging

## Production Deployment

### Security Considerations

1. **Change SECRET_KEY** in `settings.py`
2. **Set DEBUG = False** for production
3. **Configure ALLOWED_HOSTS**
4. **Use environment variables** for sensitive settings
5. **Enable HTTPS** for API endpoints

### Database

- **SQLite** (development): Included by default
- **PostgreSQL** (production): Recommended for production use

### Performance

- **Database indexing**: Add indexes on frequently queried fields
- **API caching**: Implement caching for configuration data
- **Rate limiting**: Add rate limiting for API endpoints

## API Examples

### cURL Examples

```bash
# Calculate price
curl -X POST http://127.0.0.1:8000/api/calculate-price/ \
  -H "Content-Type: application/json" \
  -d '{
    "distance_km": 5.5,
    "time_hours": 1.5,
    "waiting_minutes": 10,
    "day_of_week": "monday"
  }'

# Get configurations for Monday
curl "http://127.0.0.1:8000/api/pricing-configurations/?day_of_week=monday"

# Health check
curl http://127.0.0.1:8000/api/health/
```

### Python Examples

```python
import requests

# Calculate price
response = requests.post('http://127.0.0.1:8000/api/calculate-price/', json={
    'distance_km': 5.5,
    'time_hours': 1.5,
    'waiting_minutes': 10,
    'day_of_week': 'monday'
})

data = response.json()
print(f"Total price: ₹{data['data']['total_price']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is created for evaluation purposes as specified in the requirements.

---

## Support

For questions or issues:
1. Check the API documentation at `/api/docs/`
2. Review the test cases for usage examples
3. Check Django admin interface for configuration management 