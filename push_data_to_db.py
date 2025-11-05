import json
from datetime import datetime
from logging import exception

from dateutil import tz
import dotenv
from faker import Faker
from time import sleep
import urllib.request
import urllib.parse

from utilities import auth

import random


env_values = dotenv.dotenv_values()
geo_api_key = env_values['GEO_API_KEY']

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
    "Convenience Store",
    "Breakfast restaurant",
    "Department store",
    "Book store",
    "Coffee machine supplier",
    "Kebab shop",
    "Antique store",
    "Modern European restaurant"]


fake = Faker()

user_collection = auth.create_collection_connection("Users")
shop_collection = auth.create_collection_connection("Shops")


users : dict = None

def print_first_ten_geo():
    shop_collection.create_index([("location", "2dsphere")])


    #shops = shop_collection.find({"location": {"$exists": True}}, limit=10)


    #print(list(shops))

    reference_point = {
        "type": "Point",
        "coordinates": [-6, 54.5]  # [longitude, latitude]
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
        for shop in results_list:
            print(shop)
    else:
        print("No shops in that range")




def main():
    create_users(20)

    populate_shops()

    #add_long_lat()

    #print_first_ten_geo()





def create_users(user_count : int = 50):
    user_count-=1

    if user_count <= 0:
        raise ValueError("user count can't be less than 0")





    data = [
        {
        "name" : "Patrick McGurnaghan",
        "email" : "mcgurnaghan-p1@ulster.ac.uk",
        "dob": datetime(2000, 6,23, tzinfo=tz.tzutc()).replace(microsecond=0,tzinfo=tz.tzutc()),
        "admin": True,
        "deleted": False,
        "verified": True,
        "password": auth.generate_password_hash("password"),
        "sessions" : []
        }
    ]


    for i in range(user_count):
        name = fake.name()
        person = {
        "name" : f"{name}{i}",
        "email" : name.replace(" ",".").lower() + "@fake.com",
        "dob": fake.date_time_between(datetime(1970,1,1),datetime(2000,1,1),tz.tzutc())
            .replace(hour=0,minute=0,second=0,microsecond=0,tzinfo=tz.tzutc()),
        "admin": False,
        "deleted": False,
        "password": auth.generate_password_hash(f"password{i}"),
        "sessions": [],
        "verified": True
        }
        data.append(person)


    #delete all in collection
    user_collection.drop()


    result = user_collection.insert_many(data)

    [str(_id) for _id in result.inserted_ids]

    print("Users created")


def populate_shops():
    import json

    with open('places_2025-10-16.json') as f:
        d = json.load(f)


    shops = [shop for shop in d if shop.get('categoryName') and shop.get('categoryName') in list_of_valid_stores]

    for shop in shops:
        if shop.get('categoryName'):
            shop["type"] = shop['categoryName']
            del shop['categoryName']
        if shop.get('url'):
            del shop["url"]

    reviews_each = 10
    comments_each = 10



    shop_collection.drop()


    comment_blueprint= {
    "user_id" : None,
    "message" : None,
    "time_created" : None,
    "edits": [],
    "likes" : [],
    "deleted" : False
    }


    for shop in shops:
        shop["deleted"] = False
        shop["reviews"] = make_reviews(length=reviews_each)
        shop["photo"] = None



    shop_collection.insert_many(d)



    print("shops created from json")


def add_long_lat():
    while True:
        shop = shop_collection.find_one({"location": None})

        if shop is None:
            break

        try:
            # https://geocode.maps.co
            url = f"https://geocode.maps.co/search?q={urllib.parse.quote(shop['street'])},Belfast&api_key={geo_api_key}"
            contents = urllib.request.urlopen(url).read()
            j = json.loads(contents.decode())

            if not j or "lon" not in j[0] or "lat" not in j[0]:
                print(f"Invalid response for {shop['street']}")
                continue

            location = {
                "type": "Point",
                "coordinates": [float(j[0]["lon"]), float(j[0]["lat"])]
            }

            shop_collection.update_one({"_id": shop["_id"]}, {"$set": {"location": location}})
            print(f"added lat/long to {shop["_id"]},{shop["title"]}")
            sleep(1)
        except Exception as e:
            print(f"Error geocoding {shop['street']}: {e}")
            continue

    shop_collection.update_many(
        {"location": "$exists"},
        [
            {
                "$set": {
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            {"$toDouble": {"$arrayElemAt": ["$location.coordinates", 0]}},
                            {"$toDouble": {"$arrayElemAt": ["$location.coordinates", 1]}}
                        ]
                    }
                }
            }
        ]
    )

    print("lat and long added to shops")


def make_reviews(length : int = 10, include_comments:bool=False) -> list[dict]:

    user_ids = [str(doc['_id']) for doc in user_collection.aggregate([
                {'$sample': {'size': length}}
                ])]

    #print(len(user_ids))
    review_list : list[dict] = []



    for i in range(length):

        dt= fake.date_time_between(datetime(2020,1,1),datetime(2025,11,1),tz.tzutc())


        review_list.append({
        "user_id": user_ids[i],
        "message": fake.sentence(nb_words=15),
        "score": random.randint(1,5),
        "date_created": dt,
        "date_edited": dt,
        "edits": [],
        "comments": make_comments() if include_comments else [],
        "likes": {},
        "deleted": False,
        "photo": None,
        })


    return review_list


def make_comments(length : int = 10) -> dict:
    raise exception("not implemented")


if __name__ == '__main__':

    # length = input("type 'y' to migrate db")
    #
    # if length == "y":

        main()
