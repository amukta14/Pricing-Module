#!/bin/bash

# Setup script for Pricing Module

echo "🚀 Setting up Pricing Module..."

# Create virtual environment if it doesn't exist
if [ ! -d "../pricing_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv ../pricing_env
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source ../pricing_env/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗃️ Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python manage.py shell

# Run tests
echo "🧪 Running tests..."
python manage.py test

echo "✅ Setup complete!"
echo ""
echo "🌟 Your Pricing Module is ready!"
echo ""
echo "To start the server, run:"
echo "  source ../pricing_env/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Then visit:"
echo "  📊 Admin Interface: http://127.0.0.1:8000/admin/"
echo "  📖 API Documentation: http://127.0.0.1:8000/api/docs/"
echo "  ❤️ Health Check: http://127.0.0.1:8000/api/health/"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: admin123" 