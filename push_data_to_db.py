import json
from datetime import datetime
from bson import ObjectId
from dateutil import tz
import dotenv
from faker import Faker
from time import sleep
import urllib.request
import urllib.parse
from utilities import auth
import random

env_values = dotenv.dotenv_values()
geo_api_key = env_values.get('GEO_API_KEY', '')

list_of_valid_stores = [
    "Coffee shop",
    "Cafe",
    "Convenience store",
    "Bakery",
    "Restaurant",
    "Supermarket",
    "Grocery store",
    "Furniture store",
    "Sandwich shop",
    "Bar & grill",
    "Ice cream shop",
    "Fast food restaurant",
    "Fish and chips takeaway",
    "Deli",
    "Coffee roasters",
    "Dessert shop",
    "Italian restaurant",
    "Pub",
    "Pizza restaurant",
    "Irish restaurant",
    "Family restaurant",
    "Bistro",
    "Breakfast restaurant",
    "Department store",
    "Book store",
    "Coffee machine supplier",
    "Kebab shop",
    "Antique store",
    "Modern European restaurant"
]

fake = Faker()

user_collection = auth.create_collection_connection("Users")
shop_collection = auth.create_collection_connection("Shops")


def print_first_ten_geo():
    """Test geolocation queries"""
    shop_collection.create_index([("location", "2dsphere")])

    reference_point = {
        "type": "Point",
        "coordinates": [-6.0, 54.5]  # [longitude, latitude] - Belfast area
    }

    results = shop_collection.find({
        "location": {
            "$near": {
                "$geometry": reference_point,
                "$maxDistance": 5000  # distance in meters
            }
        }
    })

    results_list = list(results)
    if results_list:
        print(f"\nFound {len(results_list)} shops within 5km:")
        for shop in results_list:
            print(f"  - {shop.get('title', 'Unnamed')} at {shop.get('street', 'Unknown location')}")
    else:
        print("No shops in that range")


def main():
    """Main execution function"""
    print("Starting database population...")

    # Create users first
    create_users(20)

    # Create shops with reviews
    populate_shops()

    # Add geolocation data
    add_long_lat()

    # Test geolocation
    print_first_ten_geo()

    print("\nDatabase population complete!")


def create_users(user_count: int = 50):
    """Create users with proper schema"""
    user_count -= 1

    if user_count <= 0:
        raise ValueError("user count can't be less than 0")

    # Admin user
    data = [{
        "name": "Patrick McGurnaghan",
        "email": "mcgurnaghan-p1@ulster.ac.uk",
        "dob": datetime(2000, 6, 23, tzinfo=tz.tzutc()).replace(microsecond=0),
        "admin": True,
        "deleted": False,
        "verified": True,
        "password": auth.generate_password_hash("Password123"),
        "sessions": []
    }]

    # Regular users
    for i in range(user_count):
        name = fake.name()
        person = {
            "name": f"{name}",
            "email": name.replace(" ", ".").lower() + f"{i}@fake.com",
            "dob": fake.date_time_between(
                datetime(1980, 1, 1),
                datetime(2005, 1, 1),
                tz.tzutc()
            ).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz.tzutc()),
            "admin": False,
            "deleted": False,
            "password": auth.generate_password_hash(f"Password{i}"),
            "sessions": [],
            "verified": True
        }
        data.append(person)

    # Clear and insert
    user_collection.drop()
    result = user_collection.insert_many(data)

    print(f"Created {len(result.inserted_ids)} users")


def populate_shops():
    """Populate shops from JSON file with proper schema"""
    try:
        with open('places_2025-10-16.json') as f:
            shops_data = json.load(f)
    except FileNotFoundError:
        print("Warning: places_2025-10-16.json not found. Creating sample shops instead.")
        create_sample_shops()
        return

    # Get user IDs
    result = user_collection.find({}, {"_id": 1})
    user_ids = [str(user["_id"]) for user in result]

    if not user_ids:
        print("Error: No users found. Create users first.")
        return

    # Filter valid shops
    shops = [
        shop for shop in shops_data
        if shop.get('categoryName') and shop.get('categoryName') in list_of_valid_stores
    ]

    print(f"Processing {len(shops)} shops from JSON...")

    # Clear existing shops
    shop_collection.drop()

    # Process each shop
    processed_shops = []
    for shop in shops:
        # Map categoryName to proper field
        if 'categoryName' in shop:
            shop['categoryName'] = shop['categoryName']

        # Remove unwanted fields
        if 'url' in shop:
            del shop['url']

        # Ensure required fields exist
        if 'title' not in shop or not shop['title']:
            shop['title'] = fake.company()

        if 'street' not in shop or not shop['street']:
            shop['street'] = fake.street_address()

        if 'city' not in shop or not shop['city']:
            shop['city'] = 'Belfast'

        # Add standard fields
        shop["owner_id"] = random.choice(user_ids)
        shop["deleted"] = False
        shop["reviews"] = make_reviews(length=random.randint(5, 15), user_ids=user_ids)
        shop["photo"] = None

        # Handle location - ensure proper GeoJSON format
        if 'location' in shop:
            if isinstance(shop['location'], dict) and 'coordinates' in shop['location']:
                # Ensure coordinates are floats and in correct order [longitude, latitude]
                coords = shop['location']['coordinates']
                shop['location'] = {
                    "type": "Point",
                    "coordinates": [float(coords[0]), float(coords[1])]
                }
            else:
                # Invalid location format, set to None
                shop['location'] = None
        else:
            shop['location'] = None

        processed_shops.append(shop)

    # Insert all shops
    if processed_shops:
        shop_collection.insert_many(processed_shops)
        print(f"Created {len(processed_shops)} shops")
    else:
        print("No valid shops to insert")


def create_sample_shops():
    """Create sample shops if JSON file not found"""
    result = user_collection.find({}, {"_id": 1})
    user_ids = [str(user["_id"]) for user in result]

    if not user_ids:
        print("Error: No users found. Create users first.")
        return

    shop_collection.drop()

    sample_shops = []
    for i in range(30):
        shop = {
            "title": fake.company(),
            "street": fake.street_address(),
            "city": random.choice(["Belfast", "Dublin", "Cork", "Galway"]),
            "categoryName": random.choice(list_of_valid_stores),
            "owner_id": random.choice(user_ids),
            "deleted": False,
            "reviews": make_reviews(length=random.randint(3, 10), user_ids=user_ids),
            "photo": None,
            "location": None
        }

        # Add optional fields randomly
        if random.random() > 0.3:
            shop["website"] = f"https://{fake.domain_name()}"

        if random.random() > 0.3:
            shop["phone"] = fake.phone_number()

        sample_shops.append(shop)

    shop_collection.insert_many(sample_shops)
    print(f"Created {len(sample_shops)} sample shops")


def add_long_lat():
    """Add geolocation data to shops that don't have it"""
    if not geo_api_key:
        print("Warning: No GEO_API_KEY found in .env file. Skipping geocoding.")
        print("Adding random coordinates for Belfast area instead...")
        add_random_coordinates()
        return

    # Create geospatial index
    try:
        shop_collection.create_index([("location", "2dsphere")])
    except:
        pass

    shops_without_location = shop_collection.count_documents({"location": None})
    print(f"\nGeocoding {shops_without_location} shops without location...")

    count = 0
    while True:
        shop = shop_collection.find_one({"location": None})

        if shop is None:
            break

        try:
            # Build query with street and city
            address = f"{shop.get('street', '')}, {shop.get('city', 'Belfast')}"
            url = f"https://geocode.maps.co/search?q={urllib.parse.quote(address)}&api_key={geo_api_key}"

            contents = urllib.request.urlopen(url).read()
            j = json.loads(contents.decode())

            if not j or "lon" not in j[0] or "lat" not in j[0]:
                print(f"  ✗ Invalid response for {shop.get('street', 'Unknown')}")
                # Set empty location so we skip it next time
                shop_collection.update_one(
                    {"_id": shop["_id"]},
                    {"$set": {"location": {"type": "Point", "coordinates": [-6.0, 54.5]}}}
                )
                continue

            location = {
                "type": "Point",
                "coordinates": [float(j[0]["lon"]), float(j[0]["lat"])]
            }

            shop_collection.update_one(
                {"_id": shop["_id"]},
                {"$set": {"location": location}}
            )

            count += 1
            print(f"Geocoded {shop.get('title', 'Unknown')} ({count}/{shops_without_location})")

            # Rate limiting
            sleep(1.1)

        except Exception as e:
            print(f"Error geocoding {shop.get('street', 'Unknown')}: {e}")
            # Set default location
            shop_collection.update_one(
                {"_id": shop["_id"]},
                {"$set": {"location": {"type": "Point", "coordinates": [-6.0, 54.5]}}}
            )
            continue

    print(f"Geocoding complete")


def add_random_coordinates():
    """Add random coordinates around Belfast for testing"""
    shops_without_location = list(shop_collection.find({"location": None}))

    for shop in shops_without_location:
        # Random coordinates around Belfast
        # Belfast center: approximately -5.93 longitude, 54.597 latitude
        lon = -5.93 + random.uniform(-0.1, 0.1)
        lat = 54.597 + random.uniform(-0.1, 0.1)

        location = {
            "type": "Point",
            "coordinates": [lon, lat]
        }

        shop_collection.update_one(
            {"_id": shop["_id"]},
            {"$set": {"location": location}}
        )

    # Create geospatial index
    try:
        shop_collection.create_index([("location", "2dsphere")])
    except:
        pass

    print(f"Added random coordinates to {len(shops_without_location)} shops")


def make_reviews(length: int = 10, user_ids=None) -> list[dict]:
    """Create sample reviews with proper schema"""
    if not user_ids or len(user_ids) == 0:
        return []

    review_list = []

    # Use unique users if possible
    num_reviews = min(length, len(user_ids))
    selected_users = random.sample(user_ids, num_reviews)

    for user_id in selected_users:
        dt = fake.date_time_between(
            datetime(2020, 1, 1),
            datetime(2025, 11, 1),
            tz.tzutc()
        )

        review = {
            "user_id": ObjectId(user_id),
            "message": fake.sentence(nb_words=random.randint(10, 30)),
            "score": random.randint(1, 5),
            "date_created": dt,
            "date_edited": dt,
            "edits": [],
            "likes": {},
            "deleted": False,
            "photo": None,
        }

        review_list.append(review)

    return review_list


if __name__ == '__main__':
    confirmation = input("Type 'y' to populate database (this will delete existing data): ")

    if confirmation.lower() == 'y':
        main()
    else:
        print("Database population cancelled.")
