# DocAppointment

DocAppointment is a doctor appointment booking system built with a Django REST backend and static HTML/CSS/JS frontend pages.

## Project Structure

- `medicare_backend/` - Django backend (API, authentication, appointments, admin)
- `templates/` - Frontend HTML pages
- `static/` - Frontend CSS and JavaScript assets

## Features

- User registration and login
- Role-based dashboards (admin, doctor, patient)
- Doctor listing and profile pages
- Patient profile and appointment pages
- JWT authentication with cookies
- Password reset flow using OTP/email

## Tech Stack

- Python 3.x
- Django
- Django REST Framework
- SimpleJWT
- MySQL
- HTML, CSS, JavaScript

## Backend Setup

1. Go to backend folder:

```bash
cd medicare_backend
```

2. Create and activate virtual environment:

```bash
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
```

3. Install required packages:

```bash
pip install django djangorestframework django-cors-headers djangorestframework-simplejwt mysqlclient python-dotenv pillow
```

4. Create environment file from example:

```bash
copy .env.example .env
```

5. Update values in `.env` (database, email, secret key).

6. Apply migrations:

```bash
python manage.py migrate
```

7. Create admin user (optional):

```bash
python manage.py createsuperuser
```

8. Run server:

```bash
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000/`.

## Frontend Usage

Open `templates/index.html` in a local static server (for example, VS Code Live Server).

Default reset-password frontend URL used by backend:

- `http://127.0.0.1:5500/templates/reset-password.html`

If you change frontend host/port/path, update `FRONTEND_RESET_PASSWORD_URL` in `.env`.

## Environment Variables

Main values (see `medicare_backend/.env.example`):

- `DEBUG`
- `SECRET_KEY`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `ALLOWED_HOSTS`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `FRONTEND_RESET_PASSWORD_URL`

## Security Note

- Never commit `.env` to GitHub.
- Use `.env.example` as a template.
- Rotate any credentials that were exposed previously.

## License

This project is for learning and development use.
