# My Mini Crypto Site

This project is a **FastAPI backend** for user management, authentication, email verification, Google OAuth, and working with cryptocurrency data from Bybit.

---

## 🚀 Features

### Users
- **User registration** with password hashing (`bcrypt`)
- **Login** with JWT authentication
- **User profile**: view, update, delete
- **Logout**
- **Admin** can add new cryptocurrencies

### Email
- **Email verification** via JWT token
- Sends a verification link to the user's email

### Google OAuth 2.0
- Login using Google
- Automatic registration for first-time users

### Cryptocurrencies
- **Retrieve historical candles**
- **WebSocket** for real-time data from Bybit

---

## 📦 Technologies
- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2](https://docs.sqlalchemy.org/)
- JWT tokens for authentication
- `bcrypt` for secure password storage
- `aiohttp` for Google OAuth requests
- WebSocket (`websockets`) for real-time cryptocurrency data
- Bybit API for crypto market data
- SQLite or other database via SQLAlchemy

---

## ⚡ Project Structure


backand/
│
├─ database/
│ ├─ database.py # Database setup
│ └─ models.py # User and Crypto models
│
├─ auth/
│ ├─ token_jwt.py # JWT creation and verification
│ ├─ google_auth.py # Google OAuth
│ └─ config.py # OAuth and secret settings
│
├─ py_models.py # Pydantic models: User, UserLogin, Update_User
├─ send_email.py # Email sending functions
├─ bbb.py # Helper functions (e.g., fetch/save crypto)
└─ main_router.py # Main FastAPI routes (register, login, profile, crypto)


1. Clone the repository:

```bash
git clone https://github.com/yourusername/my-crypto-site.git
cd my-crypto-site

python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt


Set up .env or settings.py:

OAUTH_GOOGLE_CLIENT_ID=<your_client_id>
OAUTH_GOOGLE_CLIENT_SECRET=<your_client_secret>
SECRET_KEY=<your_jwt_secret>
EMAIL_HOST=<smtp_host>
EMAIL_PORT=<smtp_port>
EMAIL_USER=<email_user>
EMAIL_PASS=<email_password>

uvicorn backand.main_router:app --reload --host 127.0.0.1 --port 1489
