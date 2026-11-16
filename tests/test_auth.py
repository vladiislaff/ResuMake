from app.extensions import db
from app.models import User


def test_register_creates_user_and_logs_them_in(client, app):
    response = client.post("/register", data={
        "full_name": "Test User",
        "email": "TEST@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Привет, Test User!" in response.get_data(as_text=True)
    with app.app_context():
        user = db.session.query(User).filter_by(email="test@example.com").one()
        assert user.password_hash != "secure-pass-123"
        assert user.check_password("secure-pass-123")


def test_register_rejects_duplicate_email_case_insensitively(client, app):
    with app.app_context():
        user = User(email="taken@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()

    response = client.post("/register", data={
        "email": "TAKEN@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    assert response.status_code == 400
    assert "уже зарегистрирован" in response.get_data(as_text=True)


def test_register_rejects_invalid_email(client):
    response = client.post("/register", data={
        "email": "not-an-email",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    assert response.status_code == 400
    assert "корректный email" in response.get_data(as_text=True)


def test_register_rejects_short_or_mismatched_password(client):
    response = client.post("/register", data={
        "email": "new@example.com",
        "password": "short",
        "password_confirm": "different",
    })
    body = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "не менее 8 символов" in body
    assert "не совпадают" in body


def test_login_accepts_valid_credentials(client, app):
    with app.app_context():
        user = User(email="login@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "LOGIN@example.com",
        "password": "secure-pass-123",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "Личный кабинет" in response.get_data(as_text=True)


def test_login_rejects_invalid_password(client, app):
    with app.app_context():
        user = User(email="login@example.com")
        user.set_password("secure-pass-123")
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", data={
        "email": "login@example.com",
        "password": "wrong-password",
    })
    assert response.status_code == 401
    assert "Неверный email или пароль" in response.get_data(as_text=True)


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_ends_session(client):
    client.post("/register", data={
        "email": "logout@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    response = client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert client.get("/dashboard").status_code == 302
