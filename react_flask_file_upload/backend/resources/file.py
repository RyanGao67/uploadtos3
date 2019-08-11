from flask_restful import Resource
from flask import Flask, request, jsonify
class FileUpload(Resource):
    def post(self):
        file = request.files['uploaded']
        filename  = request.form['project_name']
        self.upload_file_to_s3(file, 'trigger20190806', filename)
        return jsonify('hello')

    def upload_file_to_s3(self, file, bucket_name, folder, acl="public-read"):

        """
        Docs: http://boto3.readthedocs.io/en/latest/guide/s3.html
        """
        try:
            self.s3.Object('trigger20190806', folder+'/'+file.filename).put(
                ACL='public-read',
                Body=file,
                ContentType=file.content_type,
                Metadata={'test':"testt"}
            )

        except Exception as e:
            print("Something Happened: ", e)
            return e

        return "{}/{}/{}".format('http://trigger20190806.s3.amazonaws.com', folder, file.filename)