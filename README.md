# YallaMotor Backend

A Django-based backend for a vehicle marketplace platform similar to uae.yallamotor.com.

## Project Structure

The project is organized into the following Django apps:

- **users**: User management, authentication, and profiles
- **vehicles**: Vehicle data models and specifications
- **listings**: Vehicle listings and search functionality
- **inquiries**: User inquiries and messaging
- **reviews**: User reviews and ratings
- **subscriptions**: Payment and subscription management
- **notifications**: User notifications system
- **admin_panel**: Custom admin interface
- **content**: CMS functionality

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL/MySQL

### Installation

1. Clone the repository

```bash
git clone <repository-url>
cd yallamotor
```

2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a `.env` file in the project root and add the necessary environment variables (see `.env.example`).

5. Run migrations

```bash
python manage.py migrate
```

6. Create a superuser

```bash
python manage.py createsuperuser
```

7. Run the development server

```bash
python manage.py runserver
```

## API Documentation

API documentation will be available at `/api/docs/` when the server is running.

## License

[MIT](LICENSE)