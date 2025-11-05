from flask import Flask, jsonify, make_response, request

from blueprints.shops.reviews import reviews_blueprint
from blueprints.shops.shops import shops_blueprint
from blueprints.users.users import users_blueprint
from utilities.auth import is_user
app =  Flask(__name__)


api_prefix = "/api/1.0"
app.register_blueprint(users_blueprint, url_prefix=f'{api_prefix}/users')
app.register_blueprint(shops_blueprint, url_prefix=f'{api_prefix}/shops')
app.register_blueprint(reviews_blueprint, url_prefix=f'{api_prefix}/reviews')

# todo : review each jsonify in all files to make such it is a valid dictionary inputted
# this is needed because of the auth.user method appending a new token on conditions


@app.route("/", methods=["GET"])
def index():
    return make_response("Hello, world!", 200)


@app.route("/self", methods=["GET"])
@is_user
def self(*args, **kwargs):
    token = request.cookies.get('jwt')
    return jsonify(f"User '{token}', you are successfully logged in.", 200)


@app.route("/help", methods=["GET"])
def help(*args, **kwargs):
    category = request.args.get('category')

    msg = {
        "category" : "category not found please provide a 'category' in request args to get a list of api endpoints",
        "options" : ["users", "shops","reviews", "comments"],
        "root_endpoints" : ["/index", "/self", "/help"],
    }

    #todo : build the rest ofthe help mesasges
    return jsonify(msg), 200

if __name__ == "__main__":
    app.run(debug=True)
