from datetime import datetime
from functools import wraps
import importlib

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

admin_views = Blueprint("admin_views", __name__, url_prefix="/admin")


def _app_deps():
    app_module = importlib.import_module("app")
    return (
        app_module.db,
        app_module.AdminUser,
        app_module.ServiceCategory,
        app_module.ServiceItem,
        app_module.AboutPage,
        app_module.CmsBlogPost,
        app_module.slugify,
    )


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _, AdminUser, _, _, _, _, _ = _app_deps()
        admin_id = session.get("admin_user_id")
        admin = AdminUser.query.filter_by(id=admin_id, is_active=True).first() if admin_id else None
        if not admin:
            return redirect(url_for("admin_views.login"))
        return func(*args, **kwargs)

    return wrapper


@admin_views.get("/login")
def login():
    if session.get("admin_user_id"):
        return redirect(url_for("admin_views.dashboard"))
    return render_template("admin/login.html")


@admin_views.post("/login")
def login_submit():
    _, AdminUser, _, _, _, _, _ = _app_deps()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    admin = AdminUser.query.filter_by(email=email, is_active=True).first()

    if not admin or not check_password_hash(admin.password_hash, password):
        flash("Invalid credentials", "error")
        return redirect(url_for("admin_views.login"))

    session["admin_user_id"] = admin.id
    return redirect(url_for("admin_views.dashboard"))


@admin_views.post("/logout")
def logout():
    session.pop("admin_user_id", None)
    return redirect(url_for("admin_views.login"))


@admin_views.get("/")
@admin_required
def dashboard():
    _, _, ServiceCategory, ServiceItem, _, CmsBlogPost, _ = _app_deps()
    app_module = importlib.import_module("app")
    Booking = app_module.Booking
    stats = {
        "categories": ServiceCategory.query.count(),
        "services": ServiceItem.query.count(),
        "blog_total": CmsBlogPost.query.count(),
        "blog_published": CmsBlogPost.query.filter_by(status="published").count(),
        "booking_total": Booking.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_views.get("/services")
@admin_required
def services():
    _, _, ServiceCategory, ServiceItem, _, _, _ = _app_deps()
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)
    query = ServiceItem.query.join(ServiceCategory, ServiceItem.category_id == ServiceCategory.id)
    if q:
        query = query.filter(
            (ServiceItem.name.ilike(f"%{q}%")) |
            (ServiceCategory.name.ilike(f"%{q}%"))
        )
    pagination = query.order_by(ServiceItem.name.asc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/services.html", services=pagination.items, pagination=pagination, q=q)


@admin_views.post("/services/<int:service_id>/price")
@admin_required
def services_update_price(service_id):
    db, _, _, ServiceItem, _, _, _ = _app_deps()
    service = ServiceItem.query.get_or_404(service_id)
    raw_price_30 = (request.form.get("price_30") or "").strip()
    raw_price_60 = (request.form.get("price_60") or "").strip()
    raw_price_90 = (request.form.get("price_90") or "").strip()

    if not (raw_price_30 or raw_price_60 or raw_price_90):
        flash("At least one price is required", "error")
        return redirect(url_for("admin_views.services", page=request.args.get("page", 1), q=request.args.get("q", "")))

    try:
        if raw_price_30:
            value_30 = int(raw_price_30)
            if value_30 <= 0:
                raise ValueError("Price must be greater than 0")
            service.price_30 = value_30
        if raw_price_60:
            value_60 = int(raw_price_60)
            if value_60 <= 0:
                raise ValueError("Price must be greater than 0")
            service.price_60 = value_60
        if raw_price_90:
            value_90 = int(raw_price_90)
            if value_90 <= 0:
                raise ValueError("Price must be greater than 0")
            service.price_90 = value_90
    except ValueError:
        flash("Price must be a whole number greater than 0", "error")
        return redirect(url_for("admin_views.services", page=request.args.get("page", 1), q=request.args.get("q", "")))

    db.session.commit()
    flash("Price updated", "success")
    return redirect(url_for("admin_views.services", page=request.args.get("page", 1), q=request.args.get("q", "")))


@admin_views.get("/about")
@admin_required
def about():
    return redirect(url_for("admin_views.contact_us"))


@admin_views.get("/contact-us")
@admin_required
def contact_us():
    app_module = importlib.import_module("app")
    ContactMessage = app_module.ContactMessage
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template("admin/contact_us.html", messages=pagination.items, pagination=pagination)


@admin_views.get("/bookings")
@admin_required
def bookings():
    app_module = importlib.import_module("app")
    Booking = app_module.Booking
    page = request.args.get("page", 1, type=int)
    pagination = Booking.query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template("admin/bookings.html", bookings=pagination.items, pagination=pagination)


@admin_views.get("/bookings/<int:booking_id>")
@admin_required
def booking_view(booking_id):
    app_module = importlib.import_module("app")
    Booking = app_module.Booking
    booking = Booking.query.get_or_404(booking_id)
    return render_template("admin/booking_view.html", booking=booking)


@admin_views.post("/bookings/<int:booking_id>/delete")
@admin_required
def booking_delete(booking_id):
    app_module = importlib.import_module("app")
    Booking = app_module.Booking
    db = app_module.db
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted", "success")
    return redirect(url_for("admin_views.bookings"))


@admin_views.get("/blog")
@admin_required
def blog():
    _, _, _, _, _, CmsBlogPost, _ = _app_deps()
    posts = CmsBlogPost.query.order_by(CmsBlogPost.created_at.desc()).all()
    return render_template("admin/blog_list.html", posts=posts)


@admin_views.get("/blog/new")
@admin_required
def blog_new():
    return render_template("admin/blog_form.html", post=None)


@admin_views.get("/blog/<int:post_id>/edit")
@admin_required
def blog_edit(post_id):
    _, _, _, _, _, CmsBlogPost, _ = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    return render_template("admin/blog_form.html", post=post)


@admin_views.post("/blog/save")
@admin_required
def blog_save():
    db, _, _, _, _, CmsBlogPost, slugify = _app_deps()
    post_id = request.form.get("id")
    post = CmsBlogPost.query.get(int(post_id)) if post_id else CmsBlogPost()
    if not post_id:
        db.session.add(post)
        post.created_by = session.get("admin_user_id")

    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Title is required", "error")
        return redirect(url_for("admin_views.blog_new"))

    post.title = title
    post.slug = slugify(request.form.get("slug") or title)
    post.description = (request.form.get("description") or "").strip()
    post.content_html = request.form.get("content_html") or ""
    post.featured_image_url = (request.form.get("featured_image_url") or "").strip()
    post.status = request.form.get("status") or "draft"
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
    db.session.commit()

    flash("Blog post saved", "success")
    return redirect(url_for("admin_views.blog"))


@admin_views.post("/blog/<int:post_id>/delete")
@admin_required
def blog_delete(post_id):
    db, _, _, _, _, CmsBlogPost, _ = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Blog post deleted", "success")
    return redirect(url_for("admin_views.blog"))
