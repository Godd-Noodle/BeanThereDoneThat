from bson import ObjectId
from flask import blueprints, request, make_response, jsonify, Blueprint
import dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from dateutil import tz
import utilities.verify as verify
import utilities.auth as auth


users_blueprint = Blueprint('users', __name__)

env_values = dotenv.dotenv_values()
uri = env_values['MONGO_URI']
geo_api_key = env_values['GEO_API_KEY']





#create user
@users_blueprint.route('/create', methods=['POST'])
def create_user(*args, **kwargs):
    #get arguments

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





    #create user
    user_collection : MongoClient = auth.create_collection_connection(collection_name="Users")

    year, month, day  = int(_request_args['dob_year']), int(_request_args['dob_month']), int(_request_args['dob_day'])
    dob = datetime(year, month,day, tzinfo=tz.tzutc()).replace(microsecond=0,tzinfo=tz.tzutc())
    hashed_password = auth.generate_password_hash(_request_args['password'])

    new_user = {
        "email": _request_args['email'],
        "name" : _request_args['name'],
        "is_admin" : 0,
        "verified" : 0,
        "is_deleted" : 0,
        "password": hashed_password,
        "DOB": dob,
        "sessions": []
    }


    result = user_collection.insert_one(new_user)

    _id = result.inserted_id()

    token = auth.create_token()


    return jsonify({'jwt_token': token}), 201

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

@auth.verify_admin
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

def login(): pass #todo

@auth.verify_user
def logout(*args, **kwargs):
    session_datetime = request.args.get('session_exp')
    user_id = kwargs.get('user_id')

    if session_datetime is None:
        session_datetime = ...  # this session's datetime from auth


    ...


def update(): pass  #todo
def deactivate(): pass  #todo
def recover(): pass  #todo
def delete(): pass  #todo







