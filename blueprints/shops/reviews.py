import datetime
from flask import Blueprint, request, jsonify
from bson import ObjectId
from utilities import auth, verify

reviews_blueprint = Blueprint('reviews', __name__)



@reviews_blueprint.route("/", methods=['POST','PUT'])
@auth.is_user
def upsert_review(*args,**kwargs):
    user_id = kwargs.get('user_id')
    shop_id = request.args.get('shop_id')
    message = request.args.get('message')
    score = request.args.get('score')

    # Validate args
    corrections = []

    if not shop_id:
        corrections.append({"shop_id": "shop_id was not given"})

    message_corrections = verify.check_review(message)
    if message_corrections:
        corrections.append({"message": message_corrections})

    score_corrections = verify.check_review_score(score)
    if score_corrections:
        corrections.append({"score": score_corrections})

    if len(corrections) > 0:
        return jsonify({"corrections": corrections}), 400

    shops_collection = auth.create_collection_connection("Shops")

    # Check if review exists
    review_from_shop = shops_collection.find_one(
        {"_id": ObjectId(shop_id), "deleted": False, "reviews.user_id": ObjectId(user_id)},
        {"_id": 1, "reviews.$": 1}
    )

    current_time = datetime.datetime.now(tz=datetime.timezone.utc)

    if review_from_shop:
        # Update existing review - soft delete old and add new
        old_review = review_from_shop['reviews'][0]

        # Soft delete old review
        shops_collection.update_one(
            {"_id": ObjectId(shop_id), "reviews.user_id": ObjectId(user_id)},
            {"$set": {"reviews.$.deleted": 1}}
        )

        # Create new review with edit history
        review = {
            "user_id": ObjectId(user_id),
            "message": message,
            "score": int(score),
            "date_created": old_review['date_created'],
            "date_edited": current_time,
            "edits": old_review.get('edits', []) + [{
                "message": old_review['message'],
                "score": old_review['score'],
                "date": old_review['date_edited']
            }],
            "comments": old_review.get('comments', []),
            "likes": old_review.get('likes', {}),
            "deleted": 0,
            "photo": old_review.get('photo'),
        }

        shops_collection.update_one(
            {"_id": ObjectId(shop_id)},
            {"$push": {"reviews": review}}
        )
        return_message = "edited"
    else:
        # Create new review
        review = {
            "user_id": ObjectId(user_id),
            "message": message,
            "score": int(score),
            "date_created": current_time,
            "date_edited": current_time,
            "edits": [],
            "comments": [],
            "likes": {},
            "deleted": 0,
            "photo": None,
        }

        shops_collection.update_one(
            {"_id": ObjectId(shop_id)},
            {"$push": {"reviews": review}}
        )
        return_message = "created"

    return jsonify({"message": f"Review {return_message} successfully"}), 200


@reviews_blueprint.route("/", methods=['GET'])
def get_reviews():
    shop_id = request.args.get('shop_id')
    user_id = request.args.get('user_id')
    min_score = request.args.get('min_score')
    max_score = request.args.get('max_score')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    if not shop_id:
        return jsonify({"error": "shop_id is required"}), 400

    shops_collection = auth.create_collection_connection("Shops")

    # Build match conditions for reviews
    review_match = {"$eq": ["$$review.deleted", 0]}

    if user_id:
        review_match = {
            "$and": [
                review_match,
                {"$eq": ["$$review.user_id", ObjectId(user_id)]}
            ]
        }

    if min_score:
        review_match = {
            "$and": [
                review_match if isinstance(review_match, dict) and "$and" in review_match else review_match,
                {"$gte": ["$$review.score", int(min_score)]}
            ]
        }

    if max_score:
        review_match = {
            "$and": [
                review_match if isinstance(review_match, dict) and "$and" in review_match else review_match,
                {"$lte": ["$$review.score", int(max_score)]}
            ]
        }

    pipeline = [
        {"$match": {"_id": ObjectId(shop_id), "deleted": False}},
        {
            "$project": {
                "reviews": {
                    "$filter": {
                        "input": "$reviews",
                        "as": "review",
                        "cond": review_match
                    }
                }
            }
        },
        {"$unwind": "$reviews"},
        {
            "$addFields": {
                "reviews.like_count": {"$size": {"$objectToArray": "$reviews.likes"}}
            }
        },
        {"$sort": {"reviews.like_count": -1, "reviews.date_created": -1}},
        {"$skip": (page - 1) * per_page},
        {"$limit": per_page},
        {
            "$project": {
                "_id": 0,
                "review": "$reviews"
            }
        }
    ]

    reviews = list(shops_collection.aggregate(pipeline))

    return jsonify({
        "reviews": [r['review'] for r in reviews],
        "page": page,
        "per_page": per_page
    }), 200


@reviews_blueprint.route("/like", methods=['POST'])
@auth.is_user
def like_review(*args, **kwargs):
    user_id = kwargs.get('user_id')
    shop_id = request.args.get('shop_id')
    review_user_id = request.args.get('review_user_id')

    if not shop_id or not review_user_id:
        return jsonify({"error": "shop_id and review_user_id are required"}), 400

    shops_collection = auth.create_collection_connection("Shops")

    # Add like (using user_id as key in likes object)
    result = shops_collection.update_one(
        {
            "_id": ObjectId(shop_id),
            "reviews.user_id": ObjectId(review_user_id),
            "reviews.deleted": 0
        },
        {
            "$set": {
                f"reviews.$[review].likes.{user_id}": 1
            }
        },
        array_filters=[{"review.user_id": ObjectId(review_user_id), "review.deleted": 0}]
    )

    if result.modified_count == 0:
        return jsonify({"error": "Review not found or already liked"}), 404

    return jsonify({"message": "Review liked successfully"}), 200


@reviews_blueprint.route("/like", methods=['DELETE'])
@auth.is_user
def dislike_review(*args, **kwargs):
    user_id = kwargs.get('user_id')
    shop_id = request.args.get('shop_id')
    review_user_id = request.args.get('review_user_id')

    if not shop_id or not review_user_id:
        return jsonify({"error": "shop_id and review_user_id are required"}), 400

    shops_collection = auth.create_collection_connection("Shops")

    # Remove like
    result = shops_collection.update_one(
        {
            "_id": ObjectId(shop_id),
            "reviews.user_id": ObjectId(review_user_id),
            "reviews.deleted": 0
        },
        {
            "$unset": {
                f"reviews.$[review].likes.{user_id}": ""
            }
        },
        array_filters=[{"review.user_id": ObjectId(review_user_id), "review.deleted": 0}]
    )

    if result.modified_count == 0:
        return jsonify({"error": "Review not found or like not found"}), 404

    return jsonify({"message": "Like removed successfully"}), 200



def delete_review(): pass#todo

#creating a new review will soft-delete the old review
#filter with star ranges and always order by like count

