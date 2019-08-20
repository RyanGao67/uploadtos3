### Build the docker file 
* ```docker build -t s3 .```

### run container from the dockerfile 
```
sudo docker run --rm -it \
--mount type=bind,source=/home/tgao/tgao2019/platform/test/unittest,target=/app/test \
s3 \
python s3Upload.py \
--bucket montrealproject \
--username testusername \
--password setpassword \
--project project1 \
--path /app/test/large_file_600M.py \
--metadata1 fortest
```

### Build sns 
* create a topic ```s3trigger```  
* Make sure the access policy is like the following   
```
{
  "Version": "2008-10-17",
  "Id": "__default_policy_ID",
  "Statement": [
    {
      "Sid": "__default_statement_ID",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": [
        "SNS:Publish",
        "SNS:RemovePermission",
        "SNS:SetTopicAttributes",
        "SNS:DeleteTopic",
        "SNS:ListSubscriptionsByTopic",
        "SNS:GetTopicAttributes",
        "SNS:Receive",
        "SNS:AddPermission",
        "SNS:Subscribe"
      ],
      "Resource": "arn:aws:sns:ca-central-1:488359747532:s3trigger",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:s3:*:*:montrealproject"
        }
      }
    }
  ]
}
```


### Edit the s3 bucket event
* add notification put and multipart upload completed
* send to sns 

### Create subscription for sns topic 
* Use aws lambda protocol
* select function to connect

### Lambda function 1
```
import json
import boto3

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
# queue_url = "https://sqs.us-east-2.amazonaws.com/136711379516/sqstest20190806"
queue_url = "https://sqs.ca-central-1.amazonaws.com/488359747532/s3TriggerFileInfo"
aws_lambda = boto3.client("lambda", region_name="ca-central-1")
def lambda_handler(event, context):
    # TODO implement
    if event:
        s3event = json.loads(event['Records'][0]['Sns']['Message'])
        file_obj = s3event['Records'][0]
        filename = str(file_obj['s3']['object']['key'])
        fileObj = s3.get_object(Bucket = "montrealproject", Key=filename)
        # file_content = fileObj["Body"].read().decode('utf-8')
        
        response = s3.head_object(
            Bucket='montrealproject',
            Key=filename
        )
        meta = response['Metadata']
        bucket = file_obj['s3']['bucket']
        object = file_obj['s3']['object']
        print('locate please')
        print(meta)
        print(bucket)
        print(object)
        print(file_obj)
        payload = {
            "username":meta['username'],
            "description":meta['metadata1'],
            "bucketname":bucket['name'],
            "project":object['key'].split('/')[0],
            "filename":object['key'].split('/')[1],
            "filesize":object['size'],
            "eventtime":file_obj['eventTime']
        }
        res = aws_lambda.invoke(FunctionName="nexus", InvocationType="Event", Payload=json.dumps(payload))
        
    return 'hellofrom s3trigger'


```
### lambda function 2
```
import json

import psycopg2
db_host = "database-2.cgcffqcsbfox.ca-central-1.rds.amazonaws.com"
db_port = 5432
db_name = "platform"
db_user = "postgres"
db_pass = "postgres"
db_table = "file_record"
def create_conn():
    conn = None
    try:
        conn = psycopg2.connect("dbname={} user={} host={} password={}".format(db_name,db_user,db_host,db_pass))
    except:
        print("Cannot connect.")
    return conn
    
def fetch(conn, project, filename):
    result = []
    query = "select count(*) from file_record where project='{}' and filename='{}'".format(project, filename)
    print("Now executing: {}".format(query))
    cursor = conn.cursor()
    cursor.execute(query)
    raw = cursor.fetchall()
    for line in raw:
        result.append(line)
    cursor.close()
    return result[0][0]
    
# def insert_new_file(conn, query):
def update_new_file(conn, username, description, project, filename, eventtime):
    query = '''
        update file_record 
        set username='{}',
        description='{}',
        actiontime='{}'
        where project='{}' and filename='{}'
    '''.format(username, description, eventtime, project, filename)
    print('now executing: {}'.format(query))
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    
    
def insert_new_file(conn, username, description, project, filename, eventtime):
    query = '''
        insert into file_record (username, filename, description, actiontime, project)
        values ('{}','{}','{}','{}','{}')
    '''.format(username, filename, description, eventtime, project)
    print('now executing: {}'.format(query))
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    
def lambda_handler(event, context):
    print(event)
    conn = create_conn()
    result = fetch(conn,event['project'],event['filename'])
    if result==0:
        insert_new_file(conn, event['username'], event['description'], event['project'], event['filename'], event['eventtime'])
    else:
        update_new_file(conn, event['username'], event['description'], event['project'], event['filename'], event['eventtime'])
    conn.close()
    print(type(result))
    return result

```
### How to add library to lambda function
https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

* Install libraries in a new, project-local package directory with pip's --target option.
```~/my-function$ pip install --target ./package Pillow```
```~/my-function$ cd package```
```~/my-function/package$ zip -r9 ${OLDPWD}/function.zip .```
  adding: PIL/ (stored 0%)
  adding: PIL/.libs/ (stored 0%)
  adding: PIL/.libs/libfreetype-7ce95de6.so.6.16.1 (deflated 65%)
  adding: PIL/.libs/libjpeg-3fe7dfc0.so.9.3.0 (deflated 72%)
  adding: PIL/.libs/liblcms2-a6801db4.so.2.0.8 (deflated 67%)
...
Add your function code to the archive.
```~/my-function/package$ cd $OLDPWD```
```~/my-function$ zip -g function.zip function.py```
  adding: function.py (deflated 56%)
Update the function code.
```~/my-function$ aws lambda update-function-code --function-name python37 --zip-file fileb://function.zip```
{
    "FunctionName": "python37",
    "FunctionArn": "arn:aws:lambda:us-west-2:123456789012:function:python37",
    "Runtime": "python3.7",
    "Role": "arn:aws:iam::123456789012:role/lambda-role",
    "Handler": "function.handler",
    "CodeSize": 2269409,
    "Description": "",
    "Timeout": 3,
    "MemorySize": 128,
    "LastModified": "2018-11-20T20:51:35.871+0000",
    "CodeSha256": "GcZ05oeHoJi61VpQj7vCLPs8DwCXmX5sE/fE2IHsizc=",
    "Version": "$LATEST",
    "VpcConfig": {
        "SubnetIds": [],
        "SecurityGroupIds": [],
        "VpcId": ""
    },
    "TracingConfig": {
        "Mode": "Active"
    },
    "RevisionId": "a9c05ffd-8ad6-4d22-b6cd-d34a00c1702c"
}
