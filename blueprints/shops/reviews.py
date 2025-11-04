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


def get_reviews(): pass#todo
def like_review(): pass#todo
def dislike_review(): pass#todo
def update_review(): pass#todo
def delete_review(): pass#todo

#creating a new review will soft-delete the old review
#filter with star ranges and always order by like count

