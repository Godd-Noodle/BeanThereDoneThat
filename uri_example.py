from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import dotenv


def main():
    env_values = dotenv.dotenv_values()

    uri = env_values['MONGO_URI']

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)



if __name__ == '__main__':
    main()
