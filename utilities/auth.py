from functools import wraps

from jwt import JWT
import jwt
from hashlib import pbkdf2_hmac
import dotenv
from pymongo import MongoClient



# Load environment variables from the .env file
dot_env_values = dotenv.dotenv_values()
__dotenv_values = dotenv.dotenv_values()
__salt = __dotenv_values["SALT"].encode('ascii')
__iters = int(__dotenv_values["ITERS"])
__uri = __dotenv_values["URI"]

# Create a new client and connect to the server
client = MongoClient(__uri)
#create db connection to users table
def create_collection_connection(collection_name: str, database_name : str = "BTDT"):
    return client.get_database(database_name).get_collection(collection_name)

def decode_token(jwt_token : JWT):
    if "KEY" not in dot_env_values:
        raise Exception("Missing KEY in .env file")


    try:

        data =  JWT.decode(jwt_token, dot_env_values["KEY"], algorithms=["HS256"])
        return data["user_id"] if "user_id" in data else None

    except:
        return None


def generate_password_hash(password_string: str | None):

    if password_string is None:
        return None

    return pbkdf2_hmac('sha256', password_string.encode('ascii'), __salt, __iters)





def get_user(email : str, password_hash : bytes): pass





def create_token() -> JWT:

    email = request.args.get("email")
    password = request.args.get("password")
    hashed_password = generate_password_hash(password)

    user_collection = get_user(email, hashed_password)




    return JWT()

def verify_admin(jwt):
    is_valid_user, user = verify_user(jwt)

    if not is_valid_user:
        return False, user


    if not user["is_admin"]:
        return False, "User is not an admin"


def verify_user(jwt):
    user_id = decode_token(jwt)

    if user_id is None:
        return False, "no jwt token or jwt token not valid"

    user : dict = get_user(user_id)

    if user["is_deleted"]:
        return False, "user deleted"

    return True, user
