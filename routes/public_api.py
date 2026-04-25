from flask import Blueprint, jsonify, request
import importlib


public_api = Blueprint("public_api", __name__, url_prefix="/api/v1/public")


def _app_deps():
    app_module = importlib.import_module("app")
    return (
        app_module.ServiceCategory,
        app_module.AboutPage,
        app_module.CmsBlogPost,
        app_module.get_dynamic_services_data,
        app_module.get_about_page_data,
    )


@public_api.get("/services")
def public_services():
    ServiceCategory, _, _, get_dynamic_services_data, _ = _app_deps()
    categories = (
        ServiceCategory.query.filter_by(is_active=True)
        .order_by(ServiceCategory.sort_order.asc(), ServiceCategory.name.asc())
        .all()
    )
    if not categories:
        services_dict = get_dynamic_services_data()
        return jsonify(
            {
                "categories": [
                    {"name": name, "services": [{"name": svc} for svc in service_names]}
                    for name, service_names in services_dict.items()
                ]
            }
        )

    payload = []
    for category in categories:
        payload.append(
            {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "services": [
                    service.to_dict()
                    for service in category.services
                    if service.is_active
                ],
            }
        )
    return jsonify({"categories": payload})


@public_api.get("/about")
def public_about():
    _, AboutPage, _, _, get_about_page_data = _app_deps()
    about = AboutPage.query.order_by(AboutPage.id.asc()).first()
    return jsonify(about.to_dict() if about else get_about_page_data())


@public_api.get("/blog")
def public_blog():
    _, _, CmsBlogPost, _, _ = _app_deps()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(20, max(1, int(request.args.get("per_page", 10))))

    query = CmsBlogPost.query.filter_by(status="published").order_by(
        CmsBlogPost.published_at.desc().nullslast(), CmsBlogPost.created_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [post.to_dict() for post in pagination.items],
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@public_api.get("/blog/<slug>")
def public_blog_detail(slug):
    _, _, CmsBlogPost, _, _ = _app_deps()
    post = CmsBlogPost.query.filter_by(slug=slug, status="published").first_or_404()
    return jsonify(post.to_dict())


@public_api.get("/site-meta")
def public_site_meta():
    return jsonify(
        {
            "phone": "+91 7039008000",
            "email": "travaawellness@gmail.com",
            "whatsapp": "917039008000",
            "instagram": "https://instagram.com/travaa_wellness",
        }
    )
