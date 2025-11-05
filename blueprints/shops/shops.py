import io
from bson import ObjectId
from flask import blueprints, request, make_response, jsonify, Blueprint, send_file
import utilities.verify as verify
import utilities.auth as auth
from PIL import Image

shops_blueprint = Blueprint('shops', __name__)


@shops_blueprint.route('/', methods=['POST'])
@auth.is_user
def create_shop(*args,**kwargs):
    user_id = kwargs.get('user_id')
    is_admin = kwargs.get('is_admin')

    #get fields for request

    owner_id = user_id
    title = request.args.get('title')
    lat = request.args.get('latitude')
    long = request.args.get('longitude')
    website = request.args.get('website')
    phone = request.args.get('phone')
    street = request.args.get('street')
    city = request.args.get('city')
    category = request.args.get('category')

    #overwrite owner_id if admin is creating a business for some other user
    if is_admin and request.args.get('owner_id') is not None:
        owner_id = request.args.get('owner_id')



    #todo : verify fields

    corrections = []

    #required fields
    shop={
        "owner_id": owner_id,
        "title": title,
        "street" : street,
        "city" : city,
        "reviews" : [],
        "photo" : None,
        "deleted": False,
    }

    #verification of required fields
    corrections.append(verify.check_name(title))
    corrections.append(verify.check_name(street))
    corrections.append(verify.check_name(city))

    #verification of desired fields if they are present in the request
    if lat or long:
        corrections.append(verify.check_location(lat, long))
        shop["location"] = {"type" : "Point", "coordinates": [float(long), float(lat)]}

    if website:
        corrections.append(verify.check_name(website))
        shop["website"] = website

    if phone:
        corrections.append(verify.check_phone_number(phone))
        shop["phone"] = phone


    if category:

        if category not in get_types_of_shop():
            corrections.append("Not a valid category")

        shop["categoryName"] = category


    if corrections:
        return jsonify(corrections),400



    #push shop to db

    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.insert_one(shop)

    shop_id = str(shop.inserted_id)

    return jsonify({"shop_id" : shop_id}), 200

@shops_blueprint.route('/', methods=['GET'])
def get_shops(*args,**kwargs):

    #pagination
    per_page = int(request.args.get('per_page',20))
    page = int(request.args.get('page',1))

    if page < 1 or per_page < 1 :
        return jsonify({"corrections " : "pagination values cannot be less than 1"}), 400

    offset = (page-1)*per_page

    #filters todo
    filters = {}


    #order by todo
    order_by_list = ["location", "website", "categoryName", "title", "reviews"]




    #make request
    shop_collection = auth.create_collection_connection("Shops")

    filtered_shop_count  = shop_collection.count_documents(filters)

    if filtered_shop_count < offset:
        return jsonify({"corrections " : "pagination offset is greater than that of the filtered results"}), 404

    pipeline = [
    {"$match": filters},
    {"$skip": offset},
    {"$limit": per_page},
    {
        "$project": {
            "_id": 1,
            "title": 1,
            "website": 1,
            "phone": 1,
            "street": 1,
            "city": 1,
            "categoryName": 1,
            "avgScore": {"$avg": "$reviews.score"}
        }
    }
]

    shops = list(shop_collection.aggregate(pipeline))

    if len(shops) == 0:
        return jsonify({"error " : "no shops found"}), 404

    for shop in shops:
        shop["_id"] = str(shop["_id"])



    return jsonify({"shops" : shops}), 200


@shops_blueprint.route("/<shop_id>", methods=['GET'])
def get_shop(shop_id: str, *args, **kwargs):
    if shop_id is None:
        return jsonify({"corrections": "shop_id not supplied"}), 400

    shop_collection = auth.create_collection_connection("Shops")

    # Use aggregation to calculate average score
    pipeline = [
        {"$match": {"_id": ObjectId(shop_id)}},
        {"$addFields": {
            "avgScore": {"$avg": "$reviews.score"}
        }},
        {"$project": {
            "reviews": 0,  # Exclude reviews from response
            "photo" : 0,
            "_id": 0,
        }}
    ]

    result = list(shop_collection.aggregate(pipeline))

    if not result:
        return jsonify({"corrections": "shop not found"}), 404

    shop = result[0]
    return jsonify(shop), 200


@shops_blueprint.route("/<shop_id>/photo", methods=['PUT'])
@auth.is_user
def update_photo(shop_id: str, *args, **kwargs):
    photo = request.files.get('photo')

    if not photo:
        return jsonify({"error": "No photo provided"}), 400

    # Convert photo to JPEG
    photo_jpeg = Image.open(photo).convert('RGB')

    # IMPORTANT: resize() doesn't modify in place, it returns a new image
    photo_jpeg = photo_jpeg.resize((256, 256))  # Use tuple, not list

    # Save to bytes
    img_io = io.BytesIO()
    photo_jpeg.save(img_io, format='JPEG', quality=10)
    photo_bytes = img_io.getvalue()

    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})

    if shop is None:
        return jsonify({"error": "shop not found"}), 404

    if shop.get("owner_id") != kwargs["user_id"] and not kwargs["is_admin"]:
        return jsonify({"error": "You are not allowed to update this shop"}), 403

    # Store binary data
    shop_collection.update_one(
        {"_id": ObjectId(shop_id)},
        {"$set": {"photo": photo_bytes}}
    )

    return jsonify({"message": "Photo updated successfully"}), 200


@shops_blueprint.route("/<shop_id>/photo", methods=['GET'])
def get_photo(shop_id: str):
    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})

    if shop is None or "photo" not in shop:
        return jsonify({"error": "Photo not found"}), 404

    return send_file(
        io.BytesIO(shop["photo"]),
        mimetype='image/jpeg'
    )

@shops_blueprint.route("/<shop_id>/photo", methods=['DELETE'])
@auth.is_user
def delete_photo(shop_id: str, *args, **kwargs):
    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})

    if shop is None:
        return jsonify({"error": "shop not found"}), 404

    if shop.get("owner_id") != kwargs["user_id"] and not kwargs["is_admin"]:
        return jsonify({"error": "You are not allowed to update this shop"}), 403

    if "photo" not in shop:
        return jsonify({"error": "No photo to delete"}), 404

    # Remove the photo field
    shop_collection.update_one(
        {"_id": ObjectId(shop_id)},
        {"$unset": {"photo": ""}}
    )

    return jsonify({"message": "Photo deleted successfully"}), 200

def update_shop():
    pass # todo : copy shops update

@auth.is_admin
@shops_blueprint.route("/<shop_id>/delete", methods=['DELETE'])
def delete_shop(shop_id: str, *args,**kwargs):

    title = request.args.get('title')


    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})
    if shop is None:
        return jsonify({"error": "shop not found"}), 404

    if not shop["title"] == title:
        return jsonify({"error": "title doesnt match title of shop in args, shop not deleted"}), 400

    deleted_count = shop_collection.delete_one({"_id": ObjectId(shop_id)})

    if deleted_count == 0:
        return jsonify({"error": "shop not deleted"}), 500

    return jsonify({"message": f"shop '{title}' deleted successfully"}), 200

@auth.is_user
@shops_blueprint.route("/<shop_id>/deactivate", methods=['DELETE'])
def deactivate_shop(shop_id: str, *args,**kwargs):
    user_id = kwargs["user_id"]

    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})

    if shop is None:
        return jsonify({"error": "shop not found"}), 404

    if not shop["owner_id"] == user_id:
        return jsonify({"error": "user_id doesnt match shop owner_id"}), 400

    deleted_count = shop_collection.update_one({"_id": ObjectId(shop_id)},{"$set": {"deleted": True}})

    if deleted_count == 0:
        return jsonify({"error": "shop not deleted"}), 500

    return jsonify({"message": f"shop '{shop["title"]}' deleted successfully"}), 200

@auth.is_admin
def reactive_shop(shop_id: str, *args,**kwargs):
    new_owner_id = request.args.get('new_owner_id')

    shop_collection = auth.create_collection_connection("Shops")

    shop = shop_collection.find_one({"_id": ObjectId(shop_id)})

    if shop is None:
        return jsonify({"error": "shop not found"}), 404


    if not shop["deleted"]:
        return jsonify({"error": "shop is not currently deleted"}), 400

    if new_owner_id is None:
        new_owner_id = shop["owner_id"]

    changed_values = {
        "owner_id": new_owner_id,
        "deleted": False
    }

    updated_count = shop_collection.update_one({"_id": ObjectId(shop_id)}, {"$set": changed_values})

    if updated_count == 0:
        return jsonify({"error": "shop not found"}), 500

    return jsonify({"message": f"shop '{shop["title"]}' reactivated successfully"}), 200


@shops_blueprint.route('/get_types', methods=['GET'])
def get_types():
    return jsonify(get_types_of_shop()), 200

def get_types_of_shop():

    #will be useful for a dropdown on the frontend for selecting types

    shops_collection = auth.create_collection_connection("Shops")


    pipeline = [
        {
            '$group': {
                '_id': '$categoryName',
                'count': {'$sum': 1}
            }
        },
        {
            '$sort': {'count': -1}
        }
    ]

    results = shops_collection.aggregate(pipeline)

    results = [doc["_id"] for doc in results]


    return results