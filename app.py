from flask import Flask, jsonify, make_response
from blueprints.users.users import users_blueprint
app =  Flask(__name__)


api_prefix = "/api/1.0"
app.register_blueprint(users_blueprint, url_prefix=f'{api_prefix}/users')


@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Hello world</h1>", 200)


if __name__ == "__main__":
    app.run(debug=True)
