from app.extensions import db
from app.models import User, Resume, Portfolio, Subscription

def test_home_page_returns_success(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ResuMake" in response.get_data(as_text=True)

def test_user_password_is_hashed_and_verifiable(app):
    with app.app_context():
        user = User(email="test@example.com")
        user.set_password("correct-horse-battery")
        assert user.password_hash != "correct-horse-battery"
        assert user.check_password("correct-horse-battery")
        assert not user.check_password("wrong-password")

def test_user_can_have_one_portfolio(app):
    with app.app_context():
        user = User(email="portfolio@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.commit()
        portfolio = Portfolio(user_id=user.id, bio="Test bio")
        db.session.add(portfolio)
        db.session.commit()
        assert user.portfolio.id == portfolio.id

def test_subscription_plan_accepts_one(app):
    with app.app_context():
        user = User(email="one@example.com")
        user.set_password("secure-password")
        db.session.add(user)
        db.session.flush()
        subscription = Subscription(user_id=user.id, plan="one")
        db.session.add(subscription)
        db.session.commit()
        assert subscription.plan == "one"
