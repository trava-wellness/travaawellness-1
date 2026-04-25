from datetime import datetime
import os
from functools import wraps
import importlib

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

admin_api = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


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


def _require_admin():
    _, AdminUser, _, _, _, _, _ = _app_deps()
    admin_id = session.get("admin_user_id")
    if not admin_id:
        return None
    return AdminUser.query.filter_by(id=admin_id, is_active=True).first()


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        admin = _require_admin()
        if not admin:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


def _service_payload(service):
    payload = service.to_dict()
    payload["category_name"] = service.category.name if service.category else None
    return payload


@admin_api.post("/auth/login")
def login():
    _, AdminUser, _, _, _, _, _ = _app_deps()
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    admin = AdminUser.query.filter_by(email=email, is_active=True).first()
    if not admin or not check_password_hash(admin.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["admin_user_id"] = admin.id
    return jsonify({"message": "Login successful", "admin": {"id": admin.id, "email": admin.email}})


@admin_api.post("/auth/logout")
def logout():
    session.pop("admin_user_id", None)
    return jsonify({"message": "Logged out"})


@admin_api.get("/auth/me")
@admin_required
def me():
    admin = _require_admin()
    return jsonify({"id": admin.id, "email": admin.email})


@admin_api.get("/categories")
@admin_required
def list_categories():
    _, _, ServiceCategory, _, _, _, _ = _app_deps()
    categories = ServiceCategory.query.order_by(ServiceCategory.sort_order.asc(), ServiceCategory.name.asc()).all()
    return jsonify([category.to_dict() for category in categories])


@admin_api.post("/categories")
@admin_required
def create_category():
    db, _, ServiceCategory, _, _, _, slugify = _app_deps()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400

    slug = slugify(data.get("slug") or name)
    if not slug:
        return jsonify({"error": "Valid slug required"}), 400

    if ServiceCategory.query.filter(
        (ServiceCategory.name == name) | (ServiceCategory.slug == slug)
    ).first():
        return jsonify({"error": "Category already exists"}), 409

    category = ServiceCategory(
        name=name,
        slug=slug,
        sort_order=int(data.get("sort_order") or 0),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@admin_api.patch("/categories/<int:category_id>")
@admin_required
def update_category(category_id):
    db, _, ServiceCategory, _, _, _, slugify = _app_deps()
    category = ServiceCategory.query.get_or_404(category_id)
    data = request.get_json(silent=True) or {}

    if "name" in data:
        category.name = (data.get("name") or "").strip()
    if "slug" in data:
        category.slug = slugify(data.get("slug") or category.name)
    if "sort_order" in data:
        category.sort_order = int(data.get("sort_order") or 0)
    if "is_active" in data:
        category.is_active = bool(data.get("is_active"))

    db.session.commit()
    return jsonify(category.to_dict())


@admin_api.delete("/categories/<int:category_id>")
@admin_required
def delete_category(category_id):
    db, _, ServiceCategory, _, _, _, _ = _app_deps()
    category = ServiceCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Category deleted"})


@admin_api.get("/services")
@admin_required
def list_services():
    _, _, _, ServiceItem, _, _, _ = _app_deps()
    services = ServiceItem.query.order_by(ServiceItem.sort_order.asc(), ServiceItem.name.asc()).all()
    return jsonify([_service_payload(service) for service in services])


@admin_api.post("/services")
@admin_required
def create_service():
    db, _, _, ServiceItem, _, _, slugify = _app_deps()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    category_id = data.get("category_id")
    if not name or not category_id:
        return jsonify({"error": "Name and category are required"}), 400

    slug = slugify(data.get("slug") or name)
    if ServiceItem.query.filter_by(slug=slug).first():
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    service = ServiceItem(
        category_id=int(category_id),
        name=name,
        slug=slug,
        price_30=data.get("price_30"),
        price_60=data.get("price_60"),
        price_90=data.get("price_90"),
        description=data.get("description"),
        sort_order=int(data.get("sort_order") or 0),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(service)
    db.session.commit()
    return jsonify(_service_payload(service)), 201


@admin_api.patch("/services/<int:service_id>")
@admin_required
def update_service(service_id):
    db, _, _, ServiceItem, _, _, slugify = _app_deps()
    service = ServiceItem.query.get_or_404(service_id)
    data = request.get_json(silent=True) or {}

    if "category_id" in data:
        service.category_id = int(data.get("category_id"))
    if "name" in data:
        service.name = (data.get("name") or "").strip()
    if "slug" in data:
        service.slug = slugify(data.get("slug") or service.name)
    if "price_30" in data:
        service.price_30 = data.get("price_30")
    if "price_60" in data:
        service.price_60 = data.get("price_60")
    if "price_90" in data:
        service.price_90 = data.get("price_90")
    if "description" in data:
        service.description = data.get("description")
    if "sort_order" in data:
        service.sort_order = int(data.get("sort_order") or 0)
    if "is_active" in data:
        service.is_active = bool(data.get("is_active"))

    db.session.commit()
    return jsonify(_service_payload(service))


@admin_api.delete("/services/<int:service_id>")
@admin_required
def delete_service(service_id):
    db, _, _, ServiceItem, _, _, _ = _app_deps()
    service = ServiceItem.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({"message": "Service deleted"})


@admin_api.put("/services/<int:service_id>/price")
@admin_required
def update_service_price(service_id):
    db, _, _, ServiceItem, _, _, _ = _app_deps()
    data = request.get_json(silent=True) or {}
    service = ServiceItem.query.get_or_404(service_id)
    updated = False

    def parse_positive(name):
        raw = data.get(name)
        if raw is None or str(raw).strip() == "":
            return None
        value = int(raw)
        if value <= 0:
            raise ValueError(f"{name} must be greater than 0")
        return value

    try:
        value_30 = parse_positive("price_30")
        value_60 = parse_positive("price_60")
        value_90 = parse_positive("price_90")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if value_30 is not None:
        service.price_30 = value_30
        updated = True
    if value_60 is not None:
        service.price_60 = value_60
        updated = True
    if value_90 is not None:
        service.price_90 = value_90
        updated = True

    if not updated:
        return jsonify({"error": "At least one of price_30, price_60, price_90 is required"}), 400

    db.session.commit()
    return jsonify(
        {
            "id": service.id,
            "name": service.name,
            "category": service.category.name if service.category else None,
            "price_30": service.price_30,
            "price_60": service.price_60,
            "price_90": service.price_90,
        }
    )


@admin_api.get("/about")
@admin_required
def get_about():
    _, _, _, _, AboutPage, _, _ = _app_deps()
    about = AboutPage.query.order_by(AboutPage.id.asc()).first()
    return jsonify(about.to_dict() if about else {})


@admin_api.put("/about")
@admin_required
def update_about():
    db, _, _, _, AboutPage, _, _ = _app_deps()
    data = request.get_json(silent=True) or {}
    about = AboutPage.query.order_by(AboutPage.id.asc()).first()
    if not about:
        about = AboutPage()
        db.session.add(about)

    about.title = data.get("title") or about.title
    about.subtitle = data.get("subtitle")
    about.hero_image_url = data.get("hero_image_url")
    about.intro_html = data.get("intro_html") or ""
    about.mission_html = data.get("mission_html") or ""
    about.vision_html = data.get("vision_html") or ""
    about.section_json = data.get("section_json") or "{}"
    db.session.commit()
    return jsonify(about.to_dict())


@admin_api.get("/blog")
@admin_required
def list_blog():
    _, _, _, _, _, CmsBlogPost, _ = _app_deps()
    posts = CmsBlogPost.query.order_by(CmsBlogPost.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])


@admin_api.post("/blog")
@admin_required
def create_blog():
    db, _, _, _, _, CmsBlogPost, slugify = _app_deps()
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    slug = slugify(data.get("slug") or title)
    if CmsBlogPost.query.filter_by(slug=slug).first():
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    status = data.get("status") or "draft"
    post = CmsBlogPost(
        title=title,
        slug=slug,
        description=(data.get("description") or "").strip(),
        content_html=data.get("content_html") or "",
        featured_image_url=data.get("featured_image_url"),
        status=status,
        published_at=datetime.utcnow() if status == "published" else None,
        created_by=session.get("admin_user_id"),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


@admin_api.get("/blog/<int:post_id>")
@admin_required
def get_blog(post_id):
    _, _, _, _, _, CmsBlogPost, _ = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    return jsonify(post.to_dict())


@admin_api.patch("/blog/<int:post_id>")
@admin_required
def update_blog(post_id):
    db, _, _, _, _, CmsBlogPost, slugify = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        post.title = (data.get("title") or "").strip()
    if "slug" in data:
        post.slug = slugify(data.get("slug") or post.title)
    if "description" in data:
        post.description = (data.get("description") or "").strip()
    if "content_html" in data:
        post.content_html = data.get("content_html") or ""
    if "featured_image_url" in data:
        post.featured_image_url = data.get("featured_image_url")
    if "status" in data:
        post.status = data.get("status") or post.status
        if post.status == "published" and not post.published_at:
            post.published_at = datetime.utcnow()

    db.session.commit()
    return jsonify(post.to_dict())


@admin_api.patch("/blog/<int:post_id>/status")
@admin_required
def update_blog_status(post_id):
    db, _, _, _, _, CmsBlogPost, _ = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in {"draft", "published", "archived"}:
        return jsonify({"error": "Invalid status"}), 400
    post.status = status
    if status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
    db.session.commit()
    return jsonify(post.to_dict())


@admin_api.delete("/blog/<int:post_id>")
@admin_required
def delete_blog(post_id):
    db, _, _, _, _, CmsBlogPost, _ = _app_deps()
    post = CmsBlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted"})


@admin_api.post("/uploads/image")
@admin_required
def upload_image():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "Image is required"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "blog")
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, filename)
    file.save(path)
    return jsonify({"url": f"/static/uploads/blog/{filename}"})


def seed_default_admin():
    db, AdminUser, _, _, _, _, _ = _app_deps()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@travaa.local")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = AdminUser.query.filter_by(email=admin_email).first()
    if existing:
        return
    admin = AdminUser(email=admin_email, password_hash=generate_password_hash(admin_password))
    db.session.add(admin)
    db.session.commit()
