from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, UniqueConstraint
from .extensions import db, bcrypt

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(160), nullable=True)
    role = db.Column(db.String(16), nullable=False, default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),)

    resumes = db.relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    portfolio = db.relationship("Portfolio", back_populates="user", uselist=False,
                                cascade="all, delete-orphan")
    subscriptions = db.relationship("Subscription", back_populates="user",
                                    cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Template(db.Model):
    __tablename__ = "templates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    preview_path = db.Column(db.String(255), nullable=False)
    html_path = db.Column(db.String(255), nullable=False)
    css_path = db.Column(db.String(255), nullable=False)
    is_premium = db.Column(db.Boolean, nullable=False, default=False)
    resumes = db.relationship("Resume", back_populates="template")

class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True)
    title = db.Column(db.String(160), nullable=False, default="Моё резюме")
    status = db.Column(db.String(16), nullable=False, default="draft")
    slug = db.Column(db.String(120), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=utcnow, onupdate=utcnow)

    __table_args__ = (CheckConstraint("status IN ('draft', 'published')",
                                      name="ck_resumes_status"),)

    user = db.relationship("User", back_populates="resumes")
    template = db.relationship("Template", back_populates="resumes")
    sections = db.relationship("Section", back_populates="resume",
                               cascade="all, delete-orphan",
                               order_by="Section.position")
    exports = db.relationship("Export", back_populates="resume",
                              cascade="all, delete-orphan")

class Section(db.Model):
    __tablename__ = "sections"
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    section_type = db.Column(db.String(32), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    content = db.Column(db.JSON, nullable=False, default=dict)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    resume = db.relationship("Resume", back_populates="sections")

class Portfolio(db.Model):
    __tablename__ = "portfolios"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    social_links = db.Column(db.JSON, nullable=False, default=dict)
    slug = db.Column(db.String(80), unique=True, nullable=True, index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship("User", back_populates="portfolio")
    items = db.relationship("PortfolioItem", back_populates="portfolio",
                            cascade="all, delete-orphan",
                            order_by="PortfolioItem.position")

class PortfolioItem(db.Model):
    __tablename__ = "portfolio_items"
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey("portfolios.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(2048), nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    portfolio = db.relationship("Portfolio", back_populates="items")

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    plan = db.Column(db.String(16), nullable=False, default="free")
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="active")
    user = db.relationship("User", back_populates="subscriptions")

    __table_args__ = (
        CheckConstraint("plan IN ('free', 'premium', 'one')", name="ck_subscriptions_plan"),
        CheckConstraint("status IN ('active', 'expired', 'cancelled')",
                        name="ck_subscriptions_status"),
    )

class Export(db.Model):
    __tablename__ = "exports"
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    format = db.Column(db.String(16), nullable=False, default="pdf")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    resume = db.relationship("Resume", back_populates="exports")
