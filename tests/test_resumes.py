from app.extensions import db
from app.models import Resume, User


def create_user(email):
    user = User(email=email)
    user.set_password("secure-pass-123")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email):
    return client.post("/login", data={
        "email": email,
        "password": "secure-pass-123",
    })


def test_resume_list_requires_authentication(client):
    response = client.get("/resumes/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_user_can_create_resume(client, app):
    client.post("/register", data={
        "email": "creator@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    response = client.post("/resumes/new", data={"title": "Python-разработчик"})
    assert response.status_code == 302
    assert "/resumes/" in response.headers["Location"]

    with app.app_context():
        resume = db.session.query(Resume).one()
        assert resume.title == "Python-разработчик"
        assert resume.status == "draft"


def test_create_resume_rejects_empty_title(client):
    client.post("/register", data={
        "email": "empty@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    response = client.post("/resumes/new", data={"title": "   "})
    assert response.status_code == 400
    assert "не может быть пустым" in response.get_data(as_text=True)


def test_user_sees_only_own_resumes(client, app):
    client.post("/register", data={
        "email": "first@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    client.post("/resumes/new", data={"title": "Первое резюме"})
    client.post("/logout")

    with app.app_context():
        second = create_user("second@example.com")
        db.session.add(Resume(user_id=second.id, title="Чужое резюме"))
        db.session.commit()

    login(client, "first@example.com")
    response = client.get("/resumes/")
    body = response.get_data(as_text=True)
    assert "Первое резюме" in body
    assert "Чужое резюме" not in body


def test_user_can_rename_resume(client, app):
    client.post("/register", data={
        "email": "rename@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    client.post("/resumes/new", data={"title": "Старое название"})

    with app.app_context():
        resume_id = db.session.query(Resume).one().id

    response = client.post(f"/resumes/{resume_id}/edit", data={"title": "Новое название"})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Resume, resume_id).title == "Новое название"


def test_user_can_delete_resume(client, app):
    client.post("/register", data={
        "email": "delete@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    client.post("/resumes/new", data={"title": "На удаление"})

    with app.app_context():
        resume_id = db.session.query(Resume).one().id

    response = client.post(f"/resumes/{resume_id}/delete")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Resume, resume_id) is None


def test_user_cannot_open_another_users_resume(client, app):
    client.post("/register", data={
        "email": "owner@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    client.post("/logout")

    with app.app_context():
        other = create_user("other@example.com")
        resume = Resume(user_id=other.id, title="Приватное")
        db.session.add(resume)
        db.session.commit()
        resume_id = resume.id

    login(client, "owner@example.com")
    response = client.get(f"/resumes/{resume_id}")
    assert response.status_code == 404


def test_resume_edit_rejects_title_over_160_characters(client, app):
    client.post("/register", data={
        "email": "long@example.com",
        "password": "secure-pass-123",
        "password_confirm": "secure-pass-123",
    })
    client.post("/resumes/new", data={"title": "Короткое"})

    with app.app_context():
        resume_id = db.session.query(Resume).one().id

    response = client.post(
        f"/resumes/{resume_id}/edit",
        data={"title": "x" * 161},
    )
    assert response.status_code == 400
    assert "160 символов" in response.get_data(as_text=True)
