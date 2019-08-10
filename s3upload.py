import argparse
import os
import boto3
import requests
import magic
import json

class S3MultipartUpload(object):
    PART_MINIMUM = int(5e6)

    def __init__(self, 
        bucket, 
        path, 
        region, 
        profile, 
        project,
        metadata1,
        part_size=int(15e6)
        ):
        self.bucket = bucket
        self.path = path
        self.region = region
        self.profile = profile
        self.project = project
        self.key = project+'/'+os.path.basename(path)
        self.part_bytes = part_size
        self.total_bytes = os.stat(path).st_size
        self.s3_small = boto3.resource('s3')
        self.s3_large = boto3.client('s3')
        self.metadata1 = metadata1

    # upload file smaller than 100 MB
    def upload_file(self):
        with open(self.path, 'rb') as f:
            self.s3_small.Object(self.bucket, self.key).put(
                ACL='public-read',
                Body=f,
                ContentType=magic.Magic(mime=True).from_file(self.path),
                Metadata={'metadata1':self.metadata1}
            )

    # upload file larger than 100 MB
    def upload(self):
        # create multipart upload
        mpu = self.s3_large.create_multipart_upload(
            Bucket=self.bucket, 
            Key=self.key,
            Metadata={'metadata1':self.metadata1})
        mpu_id = mpu["UploadId"]
        # upload file
        parts = []
        uploaded_bytes = 0
        with open(self.path, "rb") as f:
            i = 1
            while True:
                data = f.read(self.part_bytes)
                if not len(data):
                    break
                part = self.s3_large.upload_part(
                    Body=data, 
                    Bucket=self.bucket, 
                    Key=self.key, 
                    UploadId=mpu_id, 
                    PartNumber=i)
                parts.append({"PartNumber": i, "ETag": part["ETag"]})
                uploaded_bytes += len(data)
                print("{0} of {1} uploaded ({2:.3f}%)".format(
                    uploaded_bytes, self.total_bytes,
                    as_percent(uploaded_bytes, self.total_bytes)))
                i += 1

        # complete uploading file
        result = self.s3_large.complete_multipart_upload(
            Bucket=self.bucket,
            Key=self.key,
            UploadId=mpu_id,
            MultipartUpload={"Parts": parts})
        return result
    

# Calculate the upload percent
def as_percent(num, denom):
    return float(num) / float(denom) * 100.0


# receive the arguments from command line
def parse_args():
    parser = argparse.ArgumentParser(description='Multipart upload')
    parser.add_argument('--bucket',required=True, dest='bucket')
    parser.add_argument('--path',required=True, dest='path')
    parser.add_argument('--region',dest='region', default='eu-west-1')
    parser.add_argument('--profile',dest='profile', default='None')
    parser.add_argument('--username',required=True, dest='username' )
    parser.add_argument('--password', required=True, dest='password')
    parser.add_argument('--project', required=True, dest='project')
    parser.add_argument('--metadata1', dest='metadata1')
    return parser.parse_args()


def main():
    args = parse_args()
    mpu = S3MultipartUpload(
        args.bucket,
        args.path,
        args.region,
        args.profile,
        args.project,
        args.metadata1,
        )
    # to use the service the user need to sign in to get a token
    payload = {"username":args.username, "password":args.password}
    headers = {'Content-Type': 'application/json'}
    r2 = requests.post('http://10.3.10.12:5002/auth', data=json.dumps(payload), headers=headers)
    token = r2.json()['access_token']
    # use the token get the result list of authurized projects
    headers = {'Authorization':"JWT "+token}
    res = requests.get('http://10.3.10.12:5002/api/projects', headers = headers)
    result = map(lambda item:item['project_name'], res.json()['result'])

    if args.project in result:
        if os.stat(args.path).st_size>int(100e6):
            mpu.upload()
        else:
            mpu.upload_file()


if __name__ == "__main__":
    main()