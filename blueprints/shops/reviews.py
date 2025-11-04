import datetime
from flask import Blueprint, request, jsonify
from utilities import auth

reviews_blueprint = Blueprint('reviews', __name__)





@auth.verify_user
#add path todo
def create_review():
    #get args

    #valideate args

    #push to db


    #return message to user
    return jsonify({"message" : "review created successfully"}), 200


def get_reviews(): pass#todo
def like_review(): pass#todo
def dislike_review(): pass#todo
def update_review(): pass#todo
def delete_review(): pass#todo

#creating a new review will soft-delete the old review
#filter with star ranges and always order by like count

structure = {
    "user_id": None,
    "review" : None,
    "score" : -1,
    "date_created": datetime.datetime.now(tz=datetime.timezone.utc),# do this again when calling
    "date_edited": datetime.datetime.now(tz=datetime.timezone.utc),# do this again when calling
    "edits": [],
    "comments":[],
    "likes": {},
    "deleted": 0

}