import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any
from bson import ObjectId
from dateutil.tz import tzutc
from flask import request, jsonify
import jwt
from hashlib import pbkdf2_hmac
import dotenv
from pymongo import MongoClient



# Load environment variables from the .env file
dot_env_values = dotenv.dotenv_values()
__dotenv_values = dotenv.dotenv_values()
__salt = __dotenv_values["SALT"].encode('ascii')
__iters = int(__dotenv_values["ITERS"])
__uri = __dotenv_values["MONGO_URI"]

# Create a new client and connect to the server
client = MongoClient(__uri)
#create db connection to users table
def create_collection_connection(collection_name: str, database_name : str = "BTDT"):
    return client.get_database(database_name).get_collection(collection_name)


def generate_password_hash(password_string: str | None):

    if password_string is None:
        return None

    return pbkdf2_hmac('sha256', password_string.encode('ascii'), __salt, __iters)


def create_token(payload: dict[str: Any]) -> jwt.PyJWT | None:

    try:
        token = jwt.encode(payload=payload, key=__salt, algorithm='HS256')
    except jwt.PyJWTError:
        return None
    return token

#todo : write a wrapper that adds a logger to all api calls



def verify_user(func : callable):
    """
    A wrapper that only allows access to the function if the correct user permissions from a JWT are given.

    kwargs added are user_id,name, email, session_exp, is_admin, is_verified
    """
    @wraps(func)
    def wrapper(*args, **kwargs):

        token = request.args.get('jwt')

        if token is None:
            return jsonify({"message": "Token is missing"}), 401


        try:
            jwt_values = jwt.decode(token, __salt,algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify("Token is expired"), 401
        except jwt.InvalidTokenError:
            return jsonify("Token is invalid"), 401

        if "user_id" not in jwt_values:
            return jsonify("Token is malformed, please login in again. If this problem persists, then contact support"), 401

        user_collection = create_collection_connection("Users")
        this_user = user_collection.find_one({"_id" : ObjectId(jwt_values["user_id"])})

        if this_user is None or this_user["is_deleted"]:
            return jsonify("User not found from JWT. Perhaps the account has been deleted"), 401


        if not this_user["verified"]:
            return jsonify("User has not verified their account yet"), 401


        kwargs["user_id"] = jwt_values["user_id"]
        kwargs["name"] = this_user["name"]
        kwargs["user_email"] = this_user["email"]
        kwargs["session_exp"] = jwt_values["exp"]
        kwargs["is_admin"] = this_user["is_admin"]
        kwargs["is_verified"] = this_user["verified"]

        result = func(*args, **kwargs)


        # todo : if session expiry is soon, make a new session and return appended to the request, put in try

        return result


    return wrapper



def verify_admin(func : callable):
    """
    A wrapper that only allows access to the function if the user is an admin.
    kwargs added are user_id,name, email, session_exp, is_admin, is_verified
    """
    @verify_user
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not kwargs["is_admin"]:
            return jsonify("User is not admin"), 401

        return func(*args, **kwargs)



def verify_admin(func : callable):
    """
    A wrapper that caches the result of the call with 1 min expiry
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
