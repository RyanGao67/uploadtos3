from flask_restful import Api
from flask import Flask
from flask_cors import CORS

from resources.file import FileUpload

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.secret_key = 'jose'
api = Api(app)

api.add_resource(FileUpload, '/upload')
CORS(app)

if __name__ == "__main__":
    app.run(port=5000, debug=True)