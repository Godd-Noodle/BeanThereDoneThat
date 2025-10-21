from functools import wraps
from typing import Any
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


def create_token() -> jwt.JWT: pass




def verify_user(func : callable):
    """
    A wrapper that only allows access to the function if the correct user permissions from a JWT are given.

    kwargs added are user_id,user_name session_exp, is_admin, is_verified todo : add more terms as needed


    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("verifing user")



        token = request.cookies.get('jwt')
        jwt_values = {}

        if token is None:
            return jsonify({"message": "Token is missing"}), 401



        try:
             jwt_values = (jwt.decode(token, __dotenv_values["JWT_SECRET"]))
        except jwt.ExpiredSignatureError:
            return jsonify("Token is expired"), 401
        except jwt.InvalidTokenError:
            return jsonify("Token is invalid"), 401

        # todo : verify is the user is valid by asking the db


        if "user_id" not in jwt_values:
            return jsonify("Token is malformed, please login in again. If this problem persists. contact support"), 401


        # todo : add to the kwargs


        result= func(*args, **kwargs)


        # todo : if session expiry is soon, make a new session and return appended to the request, put in try

        return result


    return wrapper



def verify_admin(jwt):
    """
    A wrapper that only allows access to the function if the user is an admin.




    """
    # todo : make this function a wrapper with check to see if kwargs[admin] is true

    ...







