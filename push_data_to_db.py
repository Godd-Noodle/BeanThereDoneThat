import json
from datetime import datetime
from dateutil import tz
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import dotenv
from faker import Faker
from hashlib import pbkdf2_hmac
from time import sleep
import urllib.request
import urllib.parse



env_values = dotenv.dotenv_values()
uri = env_values['MONGO_URI']
salt = env_values['SALT'].encode('ascii')
iters = int(env_values['ITERS'])
geo_api_key = env_values['GEO_API_KEY']

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


def create_collection_connection(collection_name: str):
    return client.get_database("BTDT").get_collection(collection_name)


def print_first_ten_geo():
    shop_collection = create_collection_connection("Shops")
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
    #create_users(10)

    #populate_businesses()

    #add_long_lat()

    print_first_ten_geo()





def create_users(user_count : int = 50):
    user_count-=1

    if user_count <= 0:
        raise ValueError("user count can't be less than 0")



    fake = Faker()

    data = [
        {
        "name" : "Patrick McGurnaghan",
        "email" : "patrickdmcgurnaghan@gmail.com",
        "dob": datetime(2000, 6,23, tzinfo=tz.tzutc()).replace(microsecond=0,tzinfo=tz.tzutc()),
        "is_admin": 1,
        "is_deleted": 0,
        "verified": 1,
        "password": passwordify("boogies"),
        }
    ]


    for i in range(10):
        name = fake.name()
        person = {
        "name" : name,
        "email" : name.replace(" ",".").lower() + "@fake.com",
        "dob": fake.date_time_between(datetime(1970,1,1),datetime(2000,1,1),tz.tzutc())
            .replace(hour=0,minute=0,second=0,microsecond=0,tzinfo=tz.tzutc()),
        "is_admin": 0,
        "is_deleted": 0,
        "password": passwordify(name.replace(" ",".").lower()),
        }
        data.append(person)

    #push data to users table in mongodb
    user_collection = create_collection_connection("Users")

    #delete all in collection
    user_collection.drop()


    user_collection.insert_many(data)

    print("Users created")


def populate_businesses():
    import json

    with open('places_2025-10-16.json') as f:
        d = json.load(f)



    # push data to users table in mongodb
    shop_collection = create_collection_connection("Shops")

    shop_collection.drop()
    shop_collection.insert_many(d)



    print("businesses created from json")


def add_long_lat():
    shop_collection = create_collection_connection("Shops")
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

    print("lat and long added to businesses")








def passwordify(psswrd: str):
    return pbkdf2_hmac('sha256', psswrd.encode('ascii'), salt, iters)



if __name__ == '__main__':

    main()
