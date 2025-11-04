import uuid

from bson import ObjectId
from flask import blueprints, request, make_response, jsonify, Blueprint
import dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
from dateutil import tz
import utilities.verify as verify
import utilities.auth as auth


users_blueprint = Blueprint('users', __name__)


#create user
@users_blueprint.route('/create', methods=['POST'])
def create_user(*args, **kwargs):
    #todo : all wrong , copy the create business stuff

    _request_args = {}


    if request.is_json:
        _request_args = request.json
    elif request.args:
        _request_args = request.args
    else:
        ... # throw error/ return bad request

    if _request_args is None:
        ... # throw error/ return bad request

    #verifiy arguments

    corrections = {}

    password_corrections = verify.check_password(_request_args['password'])
    if password_corrections:
        corrections['password'] = password_corrections

    dob_corrections = verify.check_dob(_request_args['dob_year'], _request_args['dob_month'], _request_args['dob_day'])


    name_corrections = verify.check_name(_request_args['name'].split(" "))


    if corrections is not None:
        return make_response(jsonify(corrections), 401)

    #create user. todo : create user and return token with session created
    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")



@users_blueprint.route('/<user_id>', methods=['GET'])
def get_user(*args, **kwargs):


    user_id : str = kwargs.get('user_id')

    if user_id is None:
        return make_response(jsonify({'error': 'user_id not given'}), 404)

    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")

    # todo : remove the password field being returned, needs to be in request
    #get a user but redact the password field
    user = dict(user_collection.find_one({"_id": ObjectId(user_id)}))


    if user is None:
        return make_response(jsonify({'error': 'User not found'}), 404)

    #change data to be json-able
    user["_id"] = str(user_id)
    if user["password"] is not None:
        user.pop("password")

    return jsonify(user), 200

@auth.is_admin
@users_blueprint.route('/', methods=['GET'])
def get_users(*args, **kwargs):

    # get arguments to use in filter
    users_filter = {}
    name = request.args.get('name', None) # operator is "contains"
    email = request.args.get('email', None) # operator is "contains"
    dob_partial = request.args.get('year', None), request.args.get('month', None), request.args.get('day', None)
    dob_operator = request.args.get('dob_operator', 'eq')
    deleted, verified, admin = request.args.get('is_deleted', None), request.args.get('is_verified', None), request.args.get('is_admin', None)

    if name is not None:
        users_filter['name'] = name

    if email is not None:
        users_filter['email'] = email



    dob = None
    # figure out a system for 1 but not all is set and return a correction
    if len([True for time_step in dob_partial if time_step is not None]) in (1,2):
        return jsonify({'error': 'all fields of year, month and day must be passed'}), 404

    if len([True for time_step in dob_partial if time_step is not None]) == 3:
        year, month, day = int(dob_partial[0]), int(dob_partial[1]), int(dob_partial[2])
        if dob_operator not in ("eq", "ne", "lt","lte","gt","gte"):
            return jsonify({'error': 'invalid operator'}), 404

        if not verify.check_date(int(year), int(month), int(day)):
            return make_response(jsonify({'error': 'invalid date'}), 404)

        dob = datetime(int(year), int(month), int(day), tzinfo=tz.tzutc())
        users_filter['DOB'] = {f"${dob_operator}" : dob}


    # get offsets
    user_count = 50
    offset = 0


    #make request for users
    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")

    users_cursor = user_collection.find(users_filter)

    # a list of size 0 doesn't mean an error
    # it just means you have potentially come to the end of the list

    users = list(users_cursor)


    return make_response(jsonify({'users': users}), 200)

@users_blueprint.route('/login', methods=['POST'])
def login(*args, **kwargs):
    user_email = request.authorization.get('username', None)

    password = request.authorization.get('password', None)

    if not  user_email:
        return make_response(jsonify({'error': 'email not given'}), 401)

    if not password:
        return make_response(jsonify({'error': 'password not given'}), 401)

    hashed_password : bytes = auth.generate_password_hash(password)

    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")

    user = user_collection.find_one({"email": user_email}, {"_id": 1, "password":1})

    if user is None:
        return make_response(jsonify({'error': 'User not found'}), 404)

    if hashed_password != user['password']:
        return make_response(jsonify({'error': 'invalid password'}), 401)

    token = auth.create_token(str(user["_id"]))

    if not token:
        return make_response(jsonify({'error': 'Error making token'}), 500)

    return jsonify({'token': token}), 200

@auth.is_user
def logout(*args, **kwargs):
    session_id = request.args.get('session_id')
    user_id = kwargs.get('user_id')

    if session_id is None:
        session_id = kwargs.get('session_id')

    # todo : get index of the datetime, and delete that session from the array

    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")
    user_collection.update_one(
        {'_id': user_id},  # Filter for the parent document
        {
            '$pull': {
                'sessions': {'session_id': session_id}
            }
        }
    )

@auth.is_user
def update(): pass #todo

@auth.is_user
def deactivate(*args, **kwargs):
    user_collection = auth.create_collection_connection(collection_name="Users")

    user = user_collection.update_one({"_id": ObjectId(kwargs['user_id'])}, {"$set": {"is_deleted": True, "sessions": []}})


    #todo : deactivate all shops related to this user



    return jsonify("User has been deactivated"), 200



@auth.is_admin
def recover():
    user_id = request.args.get('user_id')

    user_collection = auth.create_collection_connection(collection_name="Users")

    user = user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_deleted": False, "sessions": []}})

    # todo : reactivate all shops related to this user

    return jsonify("User has been reactivated"), 200




@auth.is_admin
def delete():
    user_id = request.args.get('user_id')

    user_collection = auth.create_collection_connection(collection_name="Users")

    user = user_collection.delete_one({"_id": ObjectId(user_id)})

    #todo : deactivate shops related to this user and remove the user from the owner field

    return jsonify("User has been deleted"), 200

@auth.is_user
@users_blueprint.route('/revoke_sessions', methods=['DELETE'])
def revoke_sessions(*args, **kwargs):
    user_id = kwargs.get('user_id')

    session_id = kwargs.get('session_id', str)


    user_collection = auth.create_collection_connection(collection_name="Users")

    if session_id is None:
        result = user_collection.update_one({"_id": ObjectId(user_id)}, {"sessions" : []})

    else:
        result = user_collection.update_one(
            {'_id': ObjectId(kwargs["user_id"])},
            {'$pull': {'sessions': {'session_id': session_id}}}
        )

    if result.matched_count == 0:
        return make_response(jsonify({'error': 'no sessions deleted'}), 404)
    else:
        return jsonify({"session(s) has been revoked"}), 200


