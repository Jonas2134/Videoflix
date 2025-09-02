# Videoflix Backend

![Videoflix Logo](static/logo.png)

This is the Backend for a Video Streaming Platform. This project is built using Django and Django REST Framework. It allows users to Register, Login and stream their video content via HLS.

---

## Features

- Register and Login functionality for users
- User profile activation via email
- Password reset functionality via email
- Authentication via JWT (JSON Web Tokens)
- Video upload and processing in Admin Interface
- Video streaming via HLS (HTTP Live Streaming)

---

## Tech-Stack

- Python & Django
- Django REST Framework
- SimpleJWT
- Redis & Django RQ
- FFmpeg
- PostgreSQL
- Docker
- Gunicorn
- Whitenoise
- pytest

---

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/Jonas2134/Videoflix.git
   cd Videoflix
   ```

2. Create a virtual environment
   ```bash
    # Linux/macOS
    python3 -m venv env
    source env/bin/activate
    # Windows
    python -m venv env
    env\Scripts\activate
   ```

3. Install the requirements
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create them with:
   ```bash
   cp .env.example .env
   ```
   and edit the `.env` file to configure your environment variables.
   This are the required environment variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email_user
   EMAIL_HOST_PASSWORD=your_email_user_password
   EMAIL_USE_TLS=True
   EMAIL_USE_SSL=False
   DEFAULT_FROM_EMAIL=default_from_email
   ```

5. Build the Docker images
   ```bash
   docker-compose up --build
   ```
   or
   ```bash
   docker compose up --build
   ```
   The backend.entrypoint.sh makes automatically the migrations, creates a superuser and starts the server.

**Bonus:** You want to run the Backend without Docker? No problem! Just make sure you have all the requirements installed from the `requirements.txt` file.

```bash
# Run migrations
python manage.py migrate
# Create a superuser
python manage.py createsuperuser
# Start the server
python manage.py runserver
```

---

## Start and Stop the Docker Container

To start the Docker container, when it is already created:
```bash
docker compose up -d
```
and to stop the Docker container:
```bash
docker compose down
```
When you want to pause the Docker container:
```bash
docker compose stop
```
and to restart the Docker container:
```bash
docker compose start
```

---

## Start pytest

You want to start a pytest? Just run the following command! Please make sure you have pytest installed.

\_When you run the project locally:\_
```bash
pytest
```

\_When you run the project in Docker:\_

```bash
# Start the Docker Container and open a shell
# Switch to the bash in the Docker container
docker compose exec web bash
# Now you can run pytest inside the Docker container
pytest
```

---

## API Endpoints

### Authentication

| Endpoint                             | Method   | Description                       |
|--------------------------------------|----------|-----------------------------------|
| /api/register                        | POST     | Register a new user               |
| /api/login                           | POST     | Login a user                      |
| /api/logout                          | POST     | Logout a user                     |
| /api/activate/<uid>/<token>          | GET      | Activate a user account           |
| /api/password-reset                  | POST     | Reset a user's password           |
| /api/password-confirm/<uid>/<token>  | POST     | Confirm a user's password reset   |

### Video

| Endpoint                                                 | Method   | Description                              |
|----------------------------------------------------------|----------|------------------------------------------|
| /api/video                                               | GET      | List all videos                          |
| /api/video/<int:movie_id>/<str:resolution>/index.m3u8    | GET      | Get a video by ID and resolution         |
| /api/video/<int:movie_id>/<str:resolution>/<str:segment> | GET      | Get a video segment by ID and resolution |

---
