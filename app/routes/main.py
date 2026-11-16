from flask import Blueprint, render_template
from flask_login import current_user, login_required

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
