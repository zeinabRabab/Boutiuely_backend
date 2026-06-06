"""
Seed Script — populate Boutiquely AI with realistic demo data
=============================================================
Run from the PROJECT ROOT (boutiquely-ai/):
    python -m backend.seed

Creates:
  - 2 users (admin + cashier)
  - 20 products across categories
  - 10 sample orders
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db import SessionLocal, engine, Base
import backend.models  # register all models

from backend.models.user import User, UserRole
from backend.models.product import Product
from backend.models.order import Order, OrderItem, OrderStatus
from backend.auth.jwt_handler import hash_password

Base.metadata.create_all(bind=engine)

PRODUCTS = [
    {"name": "Floral Summer Dress", "price": 59.99, "stock": 30, "category": "Dresses", "color": "pink", "tags": "summer,floral,casual,lightweight,feminine", "description": "A breezy floral dress perfect for warm summer days. Lightweight fabric with a flattering A-line silhouette."},
    {"name": "Little Black Dress", "price": 89.99, "stock": 25, "category": "Dresses", "color": "black", "tags": "classic,formal,evening,elegant,timeless", "description": "The iconic little black dress — versatile, elegant, and perfect for any occasion from office to evening out."},
    {"name": "Boho Maxi Dress", "price": 74.99, "stock": 18, "category": "Dresses", "color": "multicolor", "tags": "bohemian,maxi,casual,flowy,beach,festival", "description": "Flowy boho maxi dress with ethnic print. Perfect for beach vacations and music festivals."},
    {"name": "Striped Midi Dress", "price": 64.99, "stock": 22, "category": "Dresses", "color": "navy", "tags": "nautical,midi,casual,stripes,summer", "description": "Classic navy striped midi dress with a nautical feel. Comfortable cotton blend fabric."},
    {"name": "White Linen Shirt", "price": 39.99, "stock": 40, "category": "Tops", "color": "white", "tags": "casual,linen,summer,lightweight,basics,everyday", "description": "Breathable linen shirt ideal for summer. Relaxed fit with a classic collar."},
    {"name": "Silk Blouse", "price": 79.99, "stock": 15, "category": "Tops", "color": "beige", "tags": "formal,silk,elegant,office,premium,blouse", "description": "Luxurious silk blouse with a sophisticated drape. Perfect for the office or evening events."},
    {"name": "Crop Top Floral", "price": 29.99, "stock": 35, "category": "Tops", "color": "pink", "tags": "casual,crop,floral,summer,trendy,young", "description": "Cute floral crop top with ruffled edges. Great for pairing with high-waist jeans."},
    {"name": "High Waist Skinny Jeans", "price": 69.99, "stock": 28, "category": "Bottoms", "color": "blue", "tags": "denim,jeans,casual,skinny,everyday,classic", "description": "High-waist skinny jeans in classic blue denim. Flattering cut with stretch for all-day comfort."},
    {"name": "Pleated Midi Skirt", "price": 54.99, "stock": 20, "category": "Bottoms", "color": "beige", "tags": "elegant,midi,pleated,formal,office,feminine", "description": "Elegant pleated midi skirt in soft beige. Perfect for professional settings or brunch dates."},
    {"name": "Wide Leg Trousers", "price": 64.99, "stock": 17, "category": "Bottoms", "color": "black", "tags": "formal,wide-leg,trousers,office,chic,classic", "description": "Sleek wide-leg trousers in a tailored cut. A staple piece for any professional wardrobe."},
    {"name": "Trench Coat", "price": 149.99, "stock": 10, "category": "Outerwear", "color": "beige", "tags": "classic,trench,outerwear,timeless,fall,premium", "description": "Classic double-breasted trench coat in timeless beige. A wardrobe investment that lasts decades."},
    {"name": "Leather Jacket", "price": 179.99, "stock": 8, "category": "Outerwear", "color": "black", "tags": "edgy,leather,biker,cool,fall,premium,statement", "description": "Genuine leather biker jacket with silver hardware. Adds instant attitude to any outfit."},
    {"name": "Strappy Heels", "price": 89.99, "stock": 14, "category": "Shoes", "color": "nude", "tags": "heels,elegant,formal,strappy,feminine,date-night", "description": "Elegant strappy heels in nude tone. 3.5-inch heel with padded footbed for all-evening comfort."},
    {"name": "White Sneakers", "price": 79.99, "stock": 32, "category": "Shoes", "color": "white", "tags": "casual,sneakers,everyday,comfortable,sporty,clean", "description": "Minimalist white leather sneakers. The most versatile shoe you will ever own."},
    {"name": "Ankle Boots", "price": 119.99, "stock": 11, "category": "Shoes", "color": "brown", "tags": "boots,fall,casual,ankle,leather,western", "description": "Genuine suede ankle boots with a small block heel. Perfect for fall and winter outfits."},
    {"name": "Quilted Tote Bag", "price": 99.99, "stock": 16, "category": "Bags", "color": "black", "tags": "tote,practical,quilted,everyday,chic,medium", "description": "Spacious quilted tote bag with gold chain strap. Fits laptop, essentials, and more."},
    {"name": "Mini Crossbody Bag", "price": 69.99, "stock": 19, "category": "Bags", "color": "brown", "tags": "crossbody,mini,casual,compact,daily,trendy", "description": "Trendy mini crossbody in pebbled leather. Just enough room for your essentials."},
    {"name": "Pearl Drop Earrings", "price": 24.99, "stock": 50, "category": "Accessories", "color": "white", "tags": "pearls,earrings,elegant,feminine,classic,gift", "description": "Delicate pearl drop earrings on gold-tone hooks. A classic gift for any occasion."},
    {"name": "Floral Silk Scarf", "price": 34.99, "stock": 26, "category": "Accessories", "color": "multicolor", "tags": "scarf,silk,floral,versatile,accessory,elegant", "description": "Luxurious silk scarf with a vintage floral print. Wear it in your hair, around your neck, or on your bag."},
    {"name": "Sports Set (Top + Leggings)", "price": 64.99, "stock": 22, "category": "Activewear", "color": "purple", "tags": "activewear,sports,gym,leggings,workout,comfortable", "description": "Matching sports set with moisture-wicking fabric. High-waist leggings and cropped sports top."},
]


def seed():
    db = SessionLocal()
    try:
        # Clear existing data (dev only)
        if db.query(User).count() > 0:
            print("⚠️  Database already has data. Skipping seed to avoid duplicates.")
            print("   To re-seed, delete boutiquely_ai.db and run again.")
            return

        print("🌱 Seeding database...")

        # Create admin user
        admin = User(
            name="Admin User",
            email="admin@boutiquely.com",
            password=hash_password("admin123"),
            role=UserRole.admin,
        )
        # Create cashier user
        cashier = User(
            name="Sarah Cashier",
            email="cashier@boutiquely.com",
            password=hash_password("cashier123"),
            role=UserRole.cashier,
        )
        db.add_all([admin, cashier])
        db.flush()

        # Create products
        product_objs = []
        for p in PRODUCTS:
            obj = Product(**p)
            db.add(obj)
            product_objs.append(obj)
        db.flush()

        # Create sample orders linked to cashier
        import random
        from datetime import datetime, timedelta

        for i in range(10):
            order = Order(
                user_id=cashier.id,
                total_price=0.0,
                status=random.choice(list(OrderStatus)),
            )
            db.add(order)
            db.flush()

            selected = random.sample(product_objs[:12], k=random.randint(1, 3))
            total = 0.0
            for prod in selected:
                qty = random.randint(1, 2)
                db.add(OrderItem(
                    order_id=order.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=prod.price,
                ))
                total += prod.price * qty
            order.total_price = round(total, 2)

        db.commit()
        print("✅ Seed complete!")
        print("   👤 Admin:   admin@boutiquely.com / admin123")
        print("   👤 Cashier: cashier@boutiquely.com / cashier123")
        print(f"   📦 {len(PRODUCTS)} products created")
        print("   🛒 10 sample orders created")
        print("\n🚀 Start the backend: uvicorn backend.main:app --reload")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
