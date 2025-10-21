from flask import Flask, jsonify, make_response, request
from blueprints.users.users import users_blueprint
from utilities.auth import verify_user
app =  Flask(__name__)


api_prefix = "/api/1.0"
app.register_blueprint(users_blueprint, url_prefix=f'{api_prefix}/users')

#todo : add businesses, review and comments blueprints


@app.route("/", methods=["GET"])
def index():
    return make_response("Hello, world!", 200)


@app.route("/self", methods=["GET"])
@verify_user
def self(*args, **kwargs):
    token = request.cookies.get('jwt')
    return jsonify(f"User '{token}', you are successfully logged in.", 200)



if __name__ == "__main__":
    app.run(debug=True)
