from flask import Flask, render_template, request, redirect, send_from_directory, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timedelta
import urllib.parse
import os
import re
import sys
from config import Config

# When running `python app.py`, expose this module as `app`
# so route modules importing `app` don't create a second module instance.
sys.modules.setdefault("app", sys.modules[__name__])

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("FRONTEND_ORIGIN", "*")}})

# Ensure database directory exists
os.makedirs('database', exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    selected_room = db.Column(db.String(20), nullable=True, index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300))
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'content': self.content,
            'image_url': self.image_url,
            'author': self.author,
            'category': self.category,
            'created_at': self.created_at,
            'is_published': self.is_published
        }

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_title = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    service_category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_title': self.client_title,
            'content': self.content,
            'rating': self.rating,
            'service_category': self.service_category,
            'created_at': self.created_at,
            'is_featured': self.is_featured
        }


class AdminUser(db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ServiceCategory(db.Model):
    __tablename__ = "service_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    services = db.relationship(
        "ServiceItem",
        backref="category",
        lazy=True,
        order_by="ServiceItem.sort_order.asc(), ServiceItem.name.asc()",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


class ServiceItem(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("service_categories.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    price_30 = db.Column(db.Integer)
    price_60 = db.Column(db.Integer)
    price_90 = db.Column(db.Integer)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "price_30": self.price_30,
            "price_60": self.price_60,
            "price_90": self.price_90,
            "description": self.description,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


class AboutPage(db.Model):
    __tablename__ = "about_pages"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default="About Travaa Wellness")
    subtitle = db.Column(db.String(255))
    hero_image_url = db.Column(db.String(400))
    intro_html = db.Column(db.Text, default="")
    mission_html = db.Column(db.Text, default="")
    vision_html = db.Column(db.Text, default="")
    section_json = db.Column(db.Text, default="{}")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "hero_image_url": self.hero_image_url,
            "intro_html": self.intro_html,
            "mission_html": self.mission_html,
            "vision_html": self.vision_html,
            "section_json": self.section_json or "{}",
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CmsBlogPost(db.Model):
    __tablename__ = "cms_blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(220), nullable=False)
    slug = db.Column(db.String(240), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    content_html = db.Column(db.Text, nullable=False, default="")
    featured_image_url = db.Column(db.String(400))
    status = db.Column(db.String(20), nullable=False, default="draft")
    published_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("admin_users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    admin = db.relationship("AdminUser", backref="blog_posts", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "content_html": self.content_html,
            "featured_image_url": self.featured_image_url,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def purge_old_contact_messages():
    """Drop contact leads older than 10 days (light retention)."""
    cutoff = datetime.utcnow() - timedelta(days=10)
    try:
        ContactMessage.query.filter(ContactMessage.created_at < cutoff).delete(synchronize_session=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"purge_old_contact_messages: {e}")


def ensure_booking_schema():
    """Backward-compatible booking columns for older SQLite files."""
    try:
        columns = {
            row[1]
            for row in db.session.execute(db.text("PRAGMA table_info(booking)")).fetchall()
        }
        alter_statements = []
        if "location" not in columns:
            alter_statements.append("ALTER TABLE booking ADD COLUMN location VARCHAR(50)")
        if "selected_room" not in columns:
            alter_statements.append("ALTER TABLE booking ADD COLUMN selected_room VARCHAR(20)")
        if "notes" not in columns:
            alter_statements.append("ALTER TABLE booking ADD COLUMN notes TEXT")
        if "created_at" not in columns:
            alter_statements.append("ALTER TABLE booking ADD COLUMN created_at DATETIME")

        for stmt in alter_statements:
            db.session.execute(db.text(stmt))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"ensure_booking_schema: {e}")


# Create database tables
with app.app_context():
    db.create_all()
    ensure_booking_schema()
    print("Database tables created successfully!")
    purge_old_contact_messages()

# Service Data
SERVICES_DATA = {
    "Spa": [
        "Aroma Massage",
        "Swedish Massage",
        "Deep Tissue Massage",
        "Balinese Massage",
        "Thai Dry Massage",
        "Four Hand Massage",
        "Signature Massage",
        "Potly Massage",
        "Hot Stone Massage",
        "Foot Massage",
        "Back Massage",
        "Head Massage",
        "Head, Shoulder & Back Massage",
        "Hot Stone Foot Massage",
        "Herbal Massage Potli",
        "Foot Massage + Scrub",
        "Balinese Foot Ritual"
    ],
    
    "Body": [
        "Body Scrub",
        "Body Polishing & Wrap",
        "Body Scrub + Body Polishing + Body Wrap",
        "Bubble Jacuzzi",
        "Salt Bath (Single / Couple)",
        "Bath Bomb Jacuzzi",
        "Ice Bath Therapy"
    ],

    "Skin": [
        "Facial",
        "Facial Premium"
    ],

    "Nails": [
        "Cut File",
        "Normal Nail Polish",
        "Classic Manicure",
        "Classic Pedicure",
        "Aroma Pedicure",
        "Spa Pedicure",
        "Signature Pedicure",
        # Nail Extension Services
        "Gel Polish on Natural Nail",
        "Gel Polish Remover",
        "Extension Remover",
        "Overlay",
        "Refill",
        "Temporary Extension",
        "Soft Gel Extension",
        "Gel Extension",
        "Acrylic Extension",
        "Baby Boomer Extension",
        "Gum Gel Extension",
        "Per Finger Extension",
        # Nail Art Services
        "Sticker Nail Art",
        "Water Diggler Art",
        "Glitter Art",
        "French Art",
        "Chrome Art",
        "Cat Eye Art",
        "Ombre Art",
        "Line Art",
        "Foil Art",
        "Shuttle Glass Art",
        "Marble Art",
        "Swell Art",
        "2D Sweater Art",
        "3D Nail Art",
        "Jewellery Nail Art",
        "Pigment Art",
        "Spider Gel Art",
        "Animal Print Art"
    ]
}

SERVICE_PRICE_PRESET = {
    "Aroma Massage": (2400, 3000, 3600),
    "Swedish Massage": (2450, 3200, 3800),
    "Deep Tissue Massage": (2600, 3400, 4000),
    "Balinese Massage": (2600, 3400, 4000),
    "Thai Dry Massage": (2600, 3400, 4000),
    "Four Hand Massage": (5200, 6800, 8000),
    "Signature Massage": (None, 3800, 4800),
    "Herbal Massage Potli": (None, 4000, 5000),
    "Hot Stone Massage": (None, 4000, 5000),
    "Foot Massage": (1400, 2000, 2600),
    "Back Massage": (1600, 1800, 2800),
    "Head Massage": (1400, 2000, 2600),
    "Head, Shoulder & Back Massage": (1700, 2000, 2800),
    "Hot Stone Foot Massage": (1800, 2200, 3000),
    "Foot Massage + Scrub": (1600, 2000, 2400),
    "Balinese Foot Ritual": (None, 2000, 2800),
    "Facial": (None, 2400, None),
    "Facial Premium": (None, 3000, None),
    "Body Scrub": (1800, 2200, 2800),
    "Body Scrub + Body Polishing + Body Wrap": (None, 4000, 5000),
    "Bubble Jacuzzi": (None, 2400, 3000),
    "Salt Bath (Single / Couple)": (None, 900, 1800),
    "Bath Bomb Jacuzzi": (None, 1100, 2100),
    "Ice Bath Therapy": (None, 1400, 2400),
}

DEFAULT_CATEGORY_PRICING = {
    "Spa": (1800, 2600, 3400),
    "Body": (1200, 1800, 2400),
    "Skin": (1000, 1800, 2600),
    "Nails": (500, 900, 1400),
}


def get_initial_prices(category_name, service_name):
    preset = SERVICE_PRICE_PRESET.get(service_name)
    if preset:
        return preset
    return DEFAULT_CATEGORY_PRICING.get(category_name, (1000, 1500, 2200))


def seed_services_catalog():
    if ServiceCategory.query.first() or ServiceItem.query.first():
        return

    sort_category = 0
    for category_name, service_names in SERVICES_DATA.items():
        category = ServiceCategory(
            name=category_name,
            slug=slugify(category_name),
            sort_order=sort_category,
            is_active=True,
        )
        db.session.add(category)
        db.session.flush()

        for sort_service, service_name in enumerate(service_names):
            p30, p60, p90 = get_initial_prices(category_name, service_name)
            service = ServiceItem(
                category_id=category.id,
                name=service_name,
                slug=slugify(f"{category_name}-{service_name}"),
                price_30=p30,
                price_60=p60,
                price_90=p90,
                sort_order=sort_service,
                is_active=True,
            )
            db.session.add(service)
        sort_category += 1
    db.session.commit()


def backfill_missing_service_prices():
    services = ServiceItem.query.all()
    changed = False
    for service in services:
        category_name = service.category.name if service.category else ""
        p30, p60, p90 = get_initial_prices(category_name, service.name)

        if service.price_30 is None and p30 is not None:
            service.price_30 = p30
            changed = True
        if service.price_60 is None and p60 is not None:
            service.price_60 = p60
            changed = True
        if service.price_90 is None and p90 is not None:
            service.price_90 = p90
            changed = True

    if changed:
        db.session.commit()


# Sample Blog Posts Data
SAMPLE_BLOG_POSTS = [
    {
        'id': 1,
        'title': 'The Art of Mindful Wellness',
        'slug': 'art-of-mindful-wellness',
        'excerpt': 'Discover how incorporating mindfulness into your beauty routine can enhance both physical and mental wellbeing.',
        'content': 'Full blog content here...',
        'author': 'Dr. Elena Martinez',
        'category': 'Wellness',
        'image_url': '/static/images/blog1.jpg',
        'created_at': datetime(2024, 12, 1),
        'is_published': True
    },
    {
        'id': 2,
        'title': 'Latest Nail Art Trends 2024',
        'slug': 'nail-art-trends-2024',
        'excerpt': 'Explore the most sophisticated nail art designs that are taking the luxury beauty world by storm this year.',
        'content': 'Full blog content here...',
        'author': 'Master Artist Kim',
        'category': 'Nails',
        'image_url': '/static/images/blog2.jpg',
        'created_at': datetime(2024, 11, 15),
        'is_published': True
    },
    {
        'id': 3,
        'title': 'The Science of Relaxation',
        'slug': 'science-of-relaxation',
        'excerpt': 'Understanding how spa treatments affect your nervous system and promote overall health.',
        'content': 'Full blog content here...',
        'author': 'Dr. Sophia Chen',
        'category': 'Spa',
        'image_url': '/static/images/blog3.jpg',
        'created_at': datetime(2024, 11, 1),
        'is_published': True
    }
]

# Sample Testimonials Data
SAMPLE_TESTIMONIALS = [
    {
        'id': 1,
        'client_name': 'Divya Thawani',
        'client_title': 'Google Reviewer',
        'content': 'My partner and I recently treated ourselves to a couples spa massage at Travaa Wellness, and it was nothing short of a relaxing experience! The serene ambiance made the whole session feel luxurious and deeply soothing.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 12, 15),  # 1 month ago
        'is_featured': True
    },
    {
        'id': 2,
        'client_name': 'Bankmart Solutions',
        'client_title': 'Corporate Client',
        'content': 'Absolutely loved my experience at Travaa Wellness! One of the best spa sessions—luxury ambience, excellent therapists, and top-tier hospitality.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 10),  # 2 months ago
        'is_featured': True
    },
    {
        'id': 3,
        'client_name': 'Deepali Chawla',
        'client_title': 'Local Guide',
        'content': '5-star bliss! I visited Travaa Wellness and left feeling like royalty. The service, ambiance, and attention to detail were outstanding.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2025, 1, 10),  # 2 weeks ago
        'is_featured': True
    },
    {
        'id': 4,
        'client_name': 'Internship Productions',
        'client_title': 'Google Reviewer',
        'content': 'Visited Travaa Wellness for a hot stone massage and it was fantastic. Thanks to Sara for treating me like a queen. The spa is beautifully designed and super clean.',
        'rating': 5,
        'service_category': 'Massage',
        'created_at': datetime(2024, 11, 15),
        'is_featured': True
    },
    {
        'id': 5,
        'client_name': 'Pratik Pednekar',
        'client_title': 'Google Reviewer',
        'content': 'The grand opening deals were unbelievable! Amazing service, stunning ambience, and a truly luxurious experience. Highly recommended before the offers end.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 10, 15),
        'is_featured': False
    },
    {
        'id': 6,
        'client_name': 'Nalini Singh',
        'client_title': 'Google Reviewer',
        'content': 'Had a full body massage and it was incredibly relaxing. The dim lighting, pleasant aroma, and skilled therapist made the experience exceptional.',
        'rating': 5,
        'service_category': 'Massage',
        'created_at': datetime(2024, 11, 20),
        'is_featured': False
    },
    {
        'id': 7,
        'client_name': 'Tanisha Setpal',
        'client_title': 'Google Reviewer',
        'content': 'Wonderful experience! Very professional and kind staff. The place has a calming, aesthetic vibe and is extremely well maintained.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 18),
        'is_featured': False
    },
    {
        'id': 8,
        'client_name': 'Sangram',
        'client_title': 'Google Reviewer',
        'content': 'One of the most relaxing sessions ever. The therapist was skilled and the ambience was soothing and luxurious.',
        'rating': 5,
        'service_category': 'Massage',
        'created_at': datetime(2025, 1, 5),
        'is_featured': False
    },
    {
        'id': 9,
        'client_name': 'Kunal Gaikwad',
        'client_title': 'Google Reviewer',
        'content': 'Very good experience! Excellent ambience and polite staff. A must-visit for a relaxing wellness day.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2025, 1, 5),
        'is_featured': False
    },
    {
        'id': 10,
        'client_name': 'Aryan Cute',
        'client_title': 'Google Reviewer',
        'content': 'Ambience is very good, therapist is very good, and overall experience was excellent. Receptionist was also very polite.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 15),
        'is_featured': False
    },
    {
        'id': 11,
        'client_name': 'Ranjita Roy',
        'client_title': 'Google Reviewer',
        'content': 'Very good experience. Thank you so much Alino! I will visit again soon.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 10),
        'is_featured': False
    },
    {
        'id': 12,
        'client_name': 'Dhanashree Gaikwad',
        'client_title': 'Google Reviewer',
        'content': 'Loved the place! Had a great experience here.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 10),
        'is_featured': False
    },
    {
        'id': 13,
        'client_name': 'Gaurav Pawar',
        'client_title': 'Google Reviewer',
        'content': 'Nice experience, beautiful ambiance and very good service.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 12, 10),
        'is_featured': False
    },
    {
        'id': 14,
        'client_name': 'Ikshwaku Joshi',
        'client_title': 'Local Guide',
        'content': 'An absolute oasis of tranquility and professionalism!',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 10),
        'is_featured': False
    },
    {
        'id': 15,
        'client_name': 'Mubin Sultan',
        'client_title': 'Google Reviewer',
        'content': 'The service was so good!',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 5),
        'is_featured': False
    },
    {
        'id': 16,
        'client_name': 'Sarvesh Lohar',
        'client_title': 'Google Reviewer',
        'content': 'Good ambience.',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 5),
        'is_featured': False
    },
    {
        'id': 17,
        'client_name': 'OM Khochare',
        'client_title': 'Google Reviewer',
        'content': 'Great place!',
        'rating': 5,
        'service_category': 'Spa',
        'created_at': datetime(2024, 11, 5),
        'is_featured': False
    }
]

# Helper function to format date safely
def safe_strftime(date_obj, format_str):
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime(format_str)
    return ""


def get_dynamic_services_data():
    categories = (
        ServiceCategory.query.filter_by(is_active=True)
        .order_by(ServiceCategory.sort_order.asc(), ServiceCategory.name.asc())
        .all()
    )
    if not categories:
        return SERVICES_DATA

    result = {}
    for category in categories:
        services = [
            service.name
            for service in category.services
            if service.is_active
        ]
        if services:
            result[category.name] = services
    return result or SERVICES_DATA


def get_about_page_data():
    about = AboutPage.query.order_by(AboutPage.id.asc()).first()
    if about:
        return about.to_dict()

    return {
        "title": "About Travaa Wellness",
        "subtitle": "Luxury wellness, curated for balance and rejuvenation.",
        "hero_image_url": "/static/images/contact-bg.jpg",
        "intro_html": "<p>Travaa Wellness is designed as a premium wellness sanctuary where personalized care meets luxury ambience.</p>",
        "mission_html": "<p>To provide high-quality wellness experiences that support physical and mental wellbeing.</p>",
        "vision_html": "<p>To become the most trusted holistic wellness destination for families and individuals.</p>",
        "section_json": "{}",
    }


def get_published_blog_posts():
    """Published CMS rows plus built-in POSTS for any slug not already in CMS (merged, newest first)."""
    cms_posts = (
        CmsBlogPost.query.filter_by(status="published")
        .order_by(CmsBlogPost.published_at.desc().nullslast(), CmsBlogPost.created_at.desc())
        .all()
    )

    transformed = []
    cms_slugs = set()
    for post in cms_posts:
        cms_slugs.add(post.slug)
        transformed.append(
            {
                "slug": post.slug,
                "title": post.title,
                "category": "Wellness",
                "author": "Travaa Wellness Team",
                "created_at": post.published_at or post.created_at,
                "excerpt": post.description,
                "tags": [],
                "content": post.content_html,
                "image_url": post.featured_image_url,
            }
        )

    for p in POSTS:
        if p["slug"] in cms_slugs:
            continue
        transformed.append(
            {
                "slug": p["slug"],
                "title": p["title"],
                "category": p["category"],
                "author": p["author"],
                "created_at": p["created_at"],
                "excerpt": p["excerpt"],
                "tags": p.get("tags") or [],
                "content": (p.get("content") or "").strip(),
                "image_url": p.get("image_url"),
            }
        )

    transformed.sort(key=lambda x: x["created_at"], reverse=True)
    return transformed

# Routes
@app.route('/')
def home():
    featured_posts = get_published_blog_posts()[:3]
    
    # Get testimonials from database or use sample data
    try:
        testimonials = Testimonial.query.filter_by(is_featured=True).all()
        if not testimonials:
            testimonials = SAMPLE_TESTIMONIALS
        else:
            # Convert to dict format for consistency
            testimonials = [testimonial.to_dict() for testimonial in testimonials]
    except Exception as e:
        print(f"Error fetching testimonials: {e}")
        testimonials = SAMPLE_TESTIMONIALS
    
    return render_template('index.html', 
                         services=get_dynamic_services_data(),
                         posts=featured_posts,
                         testimonials=testimonials,
                         safe_strftime=safe_strftime)

@app.route('/services')
def services():
    return render_template('services.html', services=get_dynamic_services_data())


@app.route('/services-data')
def services_data():
    return jsonify(get_dynamic_services_data())

@app.route('/gallery')
def gallery():
    categories = ['Spa', 'Nails', 'Body', 'Skin']
    return render_template('gallery.html', categories=categories)

@app.route('/testimonials')
def testimonials_page():
    try:
        testimonials = Testimonial.query.filter_by(is_featured=True).all()
        if not testimonials:
            testimonials = SAMPLE_TESTIMONIALS
        else:
            testimonials = [testimonial.to_dict() for testimonial in testimonials]
    except Exception as e:
        print(f"Error fetching testimonials: {e}")
        testimonials = SAMPLE_TESTIMONIALS
    
    return render_template('testimonials.html', 
                         testimonials=testimonials,
                         safe_strftime=safe_strftime)

@app.route('/franchise', methods=['GET', 'POST'])
def franchise():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        country = request.form.get('country')
        state = request.form.get('state')
        source = request.form.get('source')
        about = request.form.get('about')

        # Prepare WhatsApp message
        message = f"""
📢 *New Franchise Inquiry - Travaa Wellness*  

👤 Name: {name}  
📧 Email: {email}  
📞 Phone: {phone}  

🌍 Country: {country}  
🏙 State: {state if state else 'Not Provided'}  

🔎 Heard About Us From: {source if source else 'Not Provided'}  

📝 About Applicant:  
{about if about else 'Not Provided'}  

Please contact them within 24 hours.
        """

        # Encode message for URL
        encoded_message = urllib.parse.quote(message)

        # WhatsApp number from config
        whatsapp_number = app.config.get("WHATSAPP_NUMBER")

        # Redirect to WhatsApp chat
        whatsapp_url = f"https://wa.me/+917039008000?text={encoded_message}"
        return redirect(whatsapp_url)

    return render_template('franchise.html')


@app.route('/about')
def about():
    return render_template("about.html", about=get_about_page_data())


from flask import Flask, render_template, abort
from datetime import datetime


POSTS = [
    {
        "slug": "travaa-wellness-luxury-destination-kharghar",
        "title": "Travaa Wellness – A Luxury Wellness Destination Coming Soon to Kharghar",
        "category": "Luxury Wellness",
        "author": "Travaa Wellness Team",
        "created_at": datetime(2025, 8, 1),
        "excerpt": "Discover how Travaa Wellness is redefining luxury wellness in Kharghar with professional therapies, family-friendly spaces, and a holistic approach to mind-body balance.",
        "tags": ["Wellness", "Spa", "Kharghar", "Luxury"],
        "content": """
        <p>In the heart of Kharghar, Navi Mumbai, Travaa Wellness is creating a new kind of wellness destination — a sanctuary where luxury meets holistic care and every visit feels like an escape.</p>

        <p>Unlike conventional spas that focus only on indulgence, Travaa Wellness is designed to enhance both physical and mental well-being. From relaxing oil massages to deeply rejuvenating Balinese therapies, each treatment is thoughtfully crafted to relieve stress, restore balance, and support overall health.</p>

        <h2>Luxury Meets Professional Care</h2>
        <p>Guests can explore a curated menu of services, including:</p>
        <ul>
            <li>Dry and oil massages for deep relaxation</li>
            <li>Deep tissue therapy for stiffness, stress, and pain relief</li>
            <li>Balinese and Thai massages for holistic healing</li>
            <li>Couple’s massages for shared wellness experiences</li>
            <li>Jacuzzi and steam baths for detoxification and indulgence</li>
            <li>Body scrubs and nail art for complete self-care</li>
        </ul>

        <p>Every therapy is administered by trained professionals, ensuring guests experience not just comfort, but true wellness benefits.</p>

        <h2>Wellness for Every Generation</h2>
        <p>Travaa Wellness believes that self-care is for everyone. With thoughtfully designed spaces like the Family Room, the spa allows parents, children, and grandparents to unwind together, turning wellness into a shared family ritual.</p>

        <h2>More Than a Spa</h2>
        <p>With calming interiors, a focus on hygiene, and personalised attention, Travaa Wellness is built as a lifestyle destination — a place where stress melts away, energy is renewed, and luxury is felt in every detail.</p>

        <p><strong>Opening on 25th August 2025</strong>, Travaa Wellness invites the Navi Mumbai community to experience wellness at a new standard of elegance and care.</p>
        """
    },
    {
        "slug": "story-behind-travaa-wellness",
        "title": "The Story Behind Travaa Wellness – A Space Created for Relaxation & Rejuvenation",
        "category": "Brand Story",
        "author": "Travaa Wellness Team",
        "created_at": datetime(2025, 8, 2),
        "excerpt": "Go behind the scenes of Travaa Wellness and discover the vision, inspiration, and philosophy that shaped this premium wellness destination.",
        "tags": ["Story", "Vision", "Wellness", "Kharghar"],
        "content": """
        <p>Travaa Wellness was born from a simple but powerful realisation: in the rush of modern life, people often forget to take care of themselves. Between work, responsibilities, and constant digital noise, true relaxation becomes rare.</p>

        <p>Travaa Wellness was created as a response to this — a space where self-care is no longer a luxury, but a necessity. Every element of the spa, from the interiors to the treatment menu, is designed to remind guests that their well-being matters.</p>

        <h2>A Space for Holistic Healing</h2>
        <p>At Travaa Wellness, the focus extends beyond physical relaxation. Therapies and treatments are thoughtfully curated to restore both the body and mind.</p>
        <p>Guests can experience:</p>
        <ul>
            <li>Thai and Balinese massages</li>
            <li>Deep tissue therapies</li>
            <li>Body scrubs and spa rituals</li>
            <li>Jacuzzi and steam sessions</li>
            <li>Nail art and grooming services</li>
        </ul>

        <p>The goal is simple — to create experiences that ease muscle tension while nurturing mental peace.</p>

        <h2>Inclusive Wellness for All</h2>
        <p>What makes Travaa truly unique is its inclusivity. With dedicated concepts like the Family Room, wellness becomes something to be shared with loved ones, making it accessible and enjoyable for every generation.</p>

        <h2>Built on Professionalism & Care</h2>
        <p>Travaa Wellness aims to be a leading brand in holistic health by combining high standards of professional care with a warm, customer-focused experience. Every treatment is carried out with precision, sensitivity, and genuine care.</p>

        <p>On <strong>25th August 2025</strong>, Travaa Wellness opens its doors in Kharghar — inviting you to step into a space built with passion, purpose, and a deep commitment to your well-being.</p>
        """
    },
    {
        "slug": "wellness-for-every-generation-family-room",
        "title": "Wellness for Every Generation: Discover the Family Room at Travaa Wellness",
        "category": "Family Wellness",
        "author": "Travaa Wellness Team",
        "created_at": datetime(2025, 8, 3),
        "excerpt": "Explore Travaa’s unique Family Room — a warm, welcoming space where parents, grandparents, and loved ones can relax and rejuvenate together.",
        "tags": ["Family", "Wellness", "Spa Experience"],
        "content": """
        <p>Self-care is often seen as something individual — a solo spa day or a personal escape. At Travaa Wellness, we believe wellness feels even more meaningful when it’s shared with the people you love.</p>

        <p>That belief inspired the creation of our <strong>Family Room</strong>, one of the most special spaces at Travaa Wellness.</p>

        <h2>A Space Designed for Togetherness</h2>
        <p>The Family Room is a warm, thoughtfully designed environment where parents, grandparents, and loved ones can unwind side by side. Instead of separate treatments in separate rooms, families can relax, reconnect, and enjoy wellness as a shared experience.</p>

        <h2>Why Wellness Belongs to Everyone</h2>
        <p>Stress, fatigue, and lifestyle challenges affect every age group. Our expert team of therapists adapts treatments with sensitivity and care, ensuring that wellness remains safe, comfortable, and enjoyable for each family member.</p>

        <p>From soothing head massages and calming foot therapies to gentle full-body relaxation, the Family Room is about making self-care inclusive.</p>

        <h2>Part of a Larger Wellness Journey</h2>
        <p>The Family Room is just one part of the premium experience at Travaa Wellness. Guests also have access to jacuzzi and steam baths, full-body massages, Balinese and Thai therapies, nail art, body scrubs, and more.</p>

        <p>Together, these offerings transform Travaa Wellness from a spa into a true wellness destination — a place where bonds are nurtured and memories are made.</p>

        <p>Opening on <strong>25th August 2025</strong> in Kharghar, Navi Mumbai, the Family Room invites you and your loved ones to experience wellness, together.</p>
        """
    },
    {
        "slug": "luxurious-experience-mind-body-soul",
        "title": "Travaa Wellness: A Luxurious Experience for Mind, Body & Soul",
        "category": "Treatments",
        "author": "Travaa Wellness Team",
        "created_at": datetime(2025, 8, 4),
        "excerpt": "Step into Travaa Wellness, where calming head massages, body scrubs, hot stone therapies, and traditional techniques come together to restore balance.",
        "tags": ["Spa Treatments", "Relaxation", "Mind Body Soul"],
        "content": """
        <p>Taking time out for yourself is no longer a luxury — it’s essential. Travaa Wellness brings this philosophy to life with a premium space in Kharghar where self-care, relaxation, and rejuvenation come together.</p>

        <h2>A Complete Wellness Experience</h2>
        <p>Every detail at Travaa Wellness is curated to support a holistic experience. From soothing head massages that melt away mental fatigue to refreshing body scrubs that brighten and renew the skin, each treatment is designed to care for both mind and body.</p>

        <p>Guests can enjoy:</p>
        <ul>
            <li>Head, foot, and full-body massages</li>
            <li>Hot stone therapies for deep relaxation</li>
            <li>Thai and Potli massages rooted in traditional healing</li>
            <li>Jacuzzi and steam baths for detox and de-stress</li>
            <li>Body scrubs and luxurious bath bomb soaks</li>
        </ul>

        <p>Experienced therapists combine technique with warmth, ensuring every guest feels truly pampered.</p>

        <h2>More Than Just a Spa</h2>
        <p>Travaa Wellness is designed as a sanctuary where luxury meets care. Minimal yet elegant interiors, private treatment spaces, and a strong focus on hygiene create an atmosphere where wellness feels personal and meaningful.</p>

        <p>Conveniently located in Kharghar and opening on <strong>25th August 2025</strong>, Travaa Wellness is ready to become the go-to destination for individuals and families seeking premium self-care experiences.</p>

        <p>Because at Travaa Wellness, it’s not just about treatments — it’s about giving you the luxurious self-care you truly deserve.</p>
        """
    },
    {
        "slug": "experience-art-of-luxury-nails",
        "title": "Experience the Art of Luxury Nails at Travaa Wellness",
        "category": "Nail Art",
        "author": "Travaa Wellness Team",
        "created_at": datetime(2025, 8, 5),
        "excerpt": "Discover how Travaa Wellness blends precision, creativity, and luxury ambience to deliver high-end nail art that reflects your style and personality.",
        "tags": ["Nail Art", "Beauty", "Self-Care"],
        "content": """
        <p>Nails are more than just a finishing touch — they’re a powerful form of self-expression. At Travaa Wellness, nail artistry is treated as both beauty and self-care.</p>

        <h2>Precision Meets Creativity</h2>
        <p>Whether you love minimal French tips, bold colours, or intricate designs, our professional nail artists are trained to create looks that reflect your personality while maintaining precision and finesse.</p>

        <p>Every service focuses not only on aesthetics but also on comfort and care. High-quality products, hygienic practices, and expert techniques ensure your nails look beautiful and feel healthy.</p>

        <h2>The Touch of Luxury You Deserve</h2>
        <p>Unlike regular salons, Travaa Wellness offers nail art in a serene, luxurious environment. Picture yourself unwinding in a calm, thoughtfully designed space while your nails are transformed into a work of art.</p>

        <h2>Part of a Complete Wellness Journey</h2>
        <p>Nail art at Travaa Wellness is just one part of a larger wellness experience. You can pair your manicure session with massage therapies, body scrubs, jacuzzi sessions, steam baths, and more — creating a complete self-care ritual.</p>

        <p>Opening on <strong>25th August 2025</strong> in Kharghar, Travaa Wellness is set to redefine what luxury nail care truly feels like.</p>
        """
    },
]


def seed_legacy_blog_posts():
    """Insert built-in POSTS into cms_blog_posts when each slug is missing so they appear in admin and stay editable."""
    try:
        existing_slugs = {row[0] for row in CmsBlogPost.query.with_entities(CmsBlogPost.slug).all()}
        any_added = False
        for p in POSTS:
            slug = p["slug"]
            if slug in existing_slugs:
                continue
            body = (p.get("content") or "").strip()
            excerpt = (p.get("excerpt") or "").strip()
            created = p.get("created_at") or datetime.utcnow()
            row = CmsBlogPost(
                title=(p.get("title") or "Untitled")[:220],
                slug=slug[:240],
                description=excerpt,
                content_html=body,
                featured_image_url=(p.get("image_url") or "").strip() or None,
                status="published",
                published_at=created,
            )
            db.session.add(row)
            existing_slugs.add(slug)
            any_added = True
        if any_added:
            db.session.commit()
            print("Seeded missing legacy blog posts into cms_blog_posts")
    except Exception as e:
        db.session.rollback()
        print(f"seed_legacy_blog_posts: {e}")


@app.route("/blog")
def blog():
    posts = get_published_blog_posts()
    categories = sorted({post["category"] for post in posts})
    return render_template("blog.html", posts=posts, categories=categories)


@app.route("/blog/<slug>")
def blog_post(slug):
    posts = get_published_blog_posts()
    post = next((p for p in posts if p["slug"] == slug), None)
    if not post:
        abort(404)

    # pass all posts so sidebar can use them as "recent"
    return render_template(
        "blog_post.html",
        post=post,
        posts=sorted(posts, key=lambda x: x["created_at"], reverse=True),
    )


@app.get("/api/v1/public/booking-availability")
def booking_availability():
    date = (request.args.get("date") or "").strip()
    time = (request.args.get("time") or "").strip()
    if not date or not time:
        return jsonify({"booked_rooms": []})

    rows = (
        Booking.query.filter_by(date=date, time=time)
        .with_entities(Booking.selected_room)
        .all()
    )
    booked = sorted({(r[0] or "").strip() for r in rows if (r[0] or "").strip()})
    return jsonify({"booked_rooms": booked})


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        try:
            name = (request.form.get('name') or '').strip()
            email = (request.form.get('email') or '').strip()
            phone = (request.form.get('phone') or '').strip()
            location = (request.form.get('location') or 'Kharghar').strip()
            category = (request.form.get('category') or '').strip()
            service = (request.form.get('service') or '').strip()
            date = (request.form.get('date') or '').strip()
            time = (request.form.get('time') or '').strip()
            selected_room = (request.form.get('selected_room') or '').strip()
            notes = (request.form.get('notes') or '').strip()
            open_wa = (request.form.get('open_whatsapp') or '').strip() == '1'

            if not all([name, email, phone, category, service, date, time, selected_room]):
                flash('Please fill all required booking fields and select a room.', 'error')
                return redirect(url_for('booking'))

            already_taken = Booking.query.filter_by(
                date=date,
                time=time,
                selected_room=selected_room,
            ).first()
            if already_taken:
                flash('Selected room is already booked for this slot. Please choose another room/time.', 'error')
                return redirect(url_for('booking'))

            booking_row = Booking(
                name=name,
                email=email,
                phone=phone,
                location=location,
                category=category,
                service=service,
                date=date,
                time=time,
                selected_room=selected_room,
                notes=notes
            )

            db.session.add(booking_row)
            db.session.commit()

            flash('Booking saved successfully. Our team will confirm your slot shortly.', 'success')
            if open_wa:
                message = f"""New Booking Request from {name}:

📍 Location: {location}
💆 Category: {category}
✨ Service: {service}
📅 Date: {date}
⏰ Time: {time}
🚪 Room: {selected_room}
📞 Phone: {phone}
📧 Email: {email}

Notes: {notes if notes else 'None'}"""
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/{app.config['WHATSAPP_NUMBER']}?text={encoded_message}"
                return redirect(url_for('booking', open_wa='1', wa_url=urllib.parse.quote(whatsapp_url, safe='')))
            return redirect(url_for('booking'))

        except Exception as e:
            print(f"Error saving booking: {e}")
            db.session.rollback()
            flash('There was an error processing your booking. Please try again.', 'error')
            return redirect(url_for('booking'))

    wa_url = None
    if (request.args.get('open_wa') or '').strip() == '1':
        wa_url = urllib.parse.unquote(request.args.get('wa_url') or '')
    return render_template('booking.html', services=get_dynamic_services_data(), wa_url=wa_url)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = (request.form.get('name') or '').strip()
            email = (request.form.get('email') or '').strip()
            subject = (request.form.get('subject') or '').strip()
            message = (request.form.get('message') or '').strip()
            if not name or not email or not subject or not message:
                flash('Please fill in all fields.', 'error')
                return redirect(url_for('contact'))

            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

            db.session.add(contact_msg)
            db.session.commit()
            purge_old_contact_messages()

            flash('Your message has been sent successfully! We will get back to you within 24 hours.', 'success')
            return redirect(url_for('contact'))

        except Exception as e:
            print(f"Error saving contact message: {e}")
            db.session.rollback()
            flash('There was an error sending your message. Please try again.', 'error')
            return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/init-sample-data')
def init_sample_data():
    """Initialize sample data in the database"""
    try:
        # Add sample testimonials
        for testimonial_data in SAMPLE_TESTIMONIALS:
            # Check if testimonial already exists
            existing = Testimonial.query.filter_by(
                client_name=testimonial_data['client_name'],
                content=testimonial_data['content']
            ).first()
            if not existing:
                testimonial = Testimonial(
                    client_name=testimonial_data['client_name'],
                    client_title=testimonial_data['client_title'],
                    content=testimonial_data['content'],
                    rating=testimonial_data['rating'],
                    service_category=testimonial_data['service_category'],
                    created_at=testimonial_data['created_at'],
                    is_featured=testimonial_data['is_featured']
                )
                db.session.add(testimonial)
        
        # Add sample blog posts
        for post_data in SAMPLE_BLOG_POSTS:
            # Check if post already exists
            existing_post = BlogPost.query.filter_by(slug=post_data['slug']).first()
            if not existing_post:
                post = BlogPost(
                    title=post_data['title'],
                    slug=post_data['slug'],
                    excerpt=post_data['excerpt'],
                    content=post_data['content'],
                    author=post_data['author'],
                    category=post_data['category'],
                    image_url=post_data.get('image_url', ''),
                    created_at=post_data['created_at'],
                    is_published=post_data['is_published']
                )
                db.session.add(post)
        
        db.session.commit()
        return """
        <h1>Sample Data Initialized Successfully!</h1>
        <p>Sample blog posts and testimonials have been added to the database.</p>
        <p><a href="/">Go to Homepage</a></p>
        """
        
    except Exception as e:
        db.session.rollback()
        return f"""
        <h1>Error Initializing Sample Data</h1>
        <p>Error: {e}</p>
        <p><a href="/">Go to Homepage</a></p>
        """
    
@app.route('/download/pricelist')
def download_pricelist():
    file_dir = os.path.join(app.root_path, 'static', 'files')
    filename = 'Travaa-Wellness-PriceList.pdf'

    # Security check: ensure file exists
    if not os.path.exists(os.path.join(file_dir, filename)):
        abort(404)

    return send_from_directory(
        directory=file_dir,
        path=filename,
        as_attachment=True
    )

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


from routes.public_api import public_api
from routes.admin_api import admin_api, seed_default_admin
from routes.admin_views import admin_views

app.register_blueprint(public_api)
app.register_blueprint(admin_api)
app.register_blueprint(admin_views)

with app.app_context():
    seed_default_admin()
    seed_services_catalog()
    backfill_missing_service_prices()
    ensure_booking_schema()
    seed_legacy_blog_posts()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("Starting Travaa Wellness Spa & Nail Art website...")
    print(f"Visit http://localhost:5000")
    print(f"To initialize sample data, visit http://localhost:5000/init-sample-data")
    
    app.run(debug=True, port=5000)