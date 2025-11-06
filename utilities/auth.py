import uuid
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId
from dateutil import tz
from flask import request, jsonify, Response


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


def create_token(user_id : str) -> jwt.PyJWT | None:
    user_collection = create_collection_connection("users")

    session_id = str(uuid.uuid4())
    cur_time = datetime.now(tz=tz.UTC)
    payload = {
        "user_id": str(user_id),
        "session_id": session_id,
        "exp": cur_time + timedelta(days=30),
    }

    user_collection.update_one({"_id": ObjectId(user_id)}, {"$push": {"sessions": payload}})

    try:
        token = jwt.encode(payload=payload, key=__salt, algorithm='HS256')
    except jwt.PyJWTError:
        return None
    return token





def is_user(func : callable):
    """
    A wrapper that only allows access to the function if the correct user permissions from a JWT are given.

    kwargs added are user_id,name, email, session_exp, is_admin, is_verified
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        #get token from authorization section, it doesn't get sent in request

        token = request.authorization.token

        #token = request.args.get('jwt')

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

        this_user = user_collection.find_one({
            '_id': ObjectId(jwt_values["user_id"]),
            'sessions.session_id': jwt_values["session_id"]
            })

        if this_user is None or this_user["is_deleted"]:
            return jsonify("User not found from JWT. Perhaps the account has been deleted"), 401


        if not this_user["verified"]:
            return jsonify("User has not verified their account yet"), 401


        kwargs["user_id"] = jwt_values["user_id"]
        kwargs["name"] = this_user["name"]
        kwargs["user_email"] = this_user["email"]
        kwargs["session_exp"] = datetime.fromtimestamp(jwt_values["exp"])
        kwargs["is_admin"] = this_user["is_admin"]
        kwargs["is_verified"] = this_user["verified"]

        result = func(*args, **kwargs)



        #checks if date to token expiry is close and if so it issues a new token
        if datetime.now() + timedelta(days=7) >= kwargs["session_exp"]:

            try:


                token = create_token(kwargs["user_id"])


                response: Response = result[0]

                response_data = eval(response.get_data())

                response_data["token"] = token

                result = jsonify(response_data)

                #removes old session id
                result = user_collection.update_one(
                    {'_id': ObjectId(kwargs["user_id"])},
                    {'$pull': {'sessions': {'session_id': jwt_values["session_id"]}}}
                )

            except:
                return result

        return result


    return wrapper



def is_admin(func : callable):
    """
    A wrapper that only allows access to the function if the user is an admin.
    kwargs added are user_id,name, email, session_exp, is_admin, is_verified
    """
    @is_user
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not kwargs["is_admin"]:
            return jsonify("User is not admin"), 401

        return func(*args, **kwargs)


def verify_password(password, db_password) -> bool:
    return True if generate_password_hash(password) == db_password else False
