import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        errors = []
        if not email or len(email) > 254 or not EMAIL_RE.fullmatch(email):
            errors.append("Укажи корректный email.")
        if len(password) < 8:
            errors.append("Пароль должен содержать не менее 8 символов.")
        if password != password_confirm:
            errors.append("Пароли не совпадают.")
        if len(full_name) > 160:
            errors.append("Имя не должно превышать 160 символов.")

        if not errors:
            existing_user = db.session.scalar(
                select(User).where(func.lower(User.email) == email)
            )
            if existing_user:
                errors.append("Пользователь с таким email уже зарегистрирован.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html", email=email, full_name=full_name), 400

        user = User(email=email, full_name=full_name or None)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Аккаунт успешно создан. Добро пожаловать!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.scalar(
            select(User).where(func.lower(User.email) == email)
        ) if email else None

        if user is None or not user.check_password(password):
            flash("Неверный email или пароль.", "danger")
            return render_template("auth/login.html", email=email), 401

        login_user(user)
        flash("Вы успешно вошли в аккаунт.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "info")
    return redirect(url_for("main.index"))
