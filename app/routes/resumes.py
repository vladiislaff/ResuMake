from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from ..extensions import db
from ..models import Resume

resumes_bp = Blueprint("resumes", __name__, url_prefix="/resumes")


def get_owned_resume_or_404(resume_id):
    resume = db.session.scalar(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
    )
    if resume is None:
        abort(404)
    return resume


@resumes_bp.get("/")
@login_required
def index():
    resumes = db.session.scalars(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.updated_at.desc(), Resume.id.desc())
    ).all()
    return render_template("resumes/index.html", resumes=resumes)


@resumes_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Название резюме не может быть пустым.", "danger")
            return render_template("resumes/form.html", resume=None, title=title), 400
        if len(title) > 160:
            flash("Название не должно превышать 160 символов.", "danger")
            return render_template("resumes/form.html", resume=None, title=title), 400

        resume = Resume(user_id=current_user.id, title=title)
        db.session.add(resume)
        db.session.commit()
        flash("Резюме создано.", "success")
        return redirect(url_for("resumes.show", resume_id=resume.id))

    return render_template("resumes/form.html", resume=None, title="")


@resumes_bp.get("/<int:resume_id>")
@login_required
def show(resume_id):
    resume = get_owned_resume_or_404(resume_id)
    return render_template("resumes/show.html", resume=resume)


@resumes_bp.route("/<int:resume_id>/edit", methods=["GET", "POST"])
@login_required
def edit(resume_id):
    resume = get_owned_resume_or_404(resume_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Название резюме не может быть пустым.", "danger")
            return render_template("resumes/form.html", resume=resume, title=title), 400
        if len(title) > 160:
            flash("Название не должно превышать 160 символов.", "danger")
            return render_template("resumes/form.html", resume=resume, title=title), 400

        resume.title = title
        db.session.commit()
        flash("Название резюме обновлено.", "success")
        return redirect(url_for("resumes.show", resume_id=resume.id))

    return render_template("resumes/form.html", resume=resume, title=resume.title)


@resumes_bp.post("/<int:resume_id>/delete")
@login_required
def delete(resume_id):
    resume = get_owned_resume_or_404(resume_id)
    db.session.delete(resume)
    db.session.commit()
    flash("Резюме удалено.", "info")
    return redirect(url_for("resumes.index"))
