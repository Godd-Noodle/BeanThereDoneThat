from flask import Flask, jsonify, make_response, request

from blueprints.shops.shops import shops_blueprint
from blueprints.users.users import users_blueprint
from utilities.auth import verify_user
app =  Flask(__name__)


api_prefix = "/api/1.0"
app.register_blueprint(users_blueprint, url_prefix=f'{api_prefix}/users')
app.register_blueprint(shops_blueprint, url_prefix=f'{api_prefix}/shops')

#todo : add review and comments blueprints


@app.route("/", methods=["GET"])
def index():
    return make_response("Hello, world!", 200)


@app.route("/self", methods=["GET"])
@verify_user
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
