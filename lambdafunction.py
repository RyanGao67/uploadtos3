import json
import boto3

s3 = boto3.client('s3')
sqs = boto3.client('sqs')
queue_url = "https://sqs.us-east-2.amazonaws.com/136711379516/sqstest20190806"

def lambda_handler(event, context):
    # TODO implement
    if event:
        print("Event:", event)
        file_obj = event['Records'][0]
        filename = str(file_obj['s3']['object']['key'])
        print('Filename:', filename)
        fileObj = s3.get_object(Bucket = "trigger20190809", Key=filename)
        # file_content = fileObj["Body"].read().decode('utf-8')
        print('locate please')
        response = sqs.send_message(
            QueueUrl= queue_url,
            DelaySeconds = 10,
            MessageBody=(json.dumps(event))
        )
        print('locate me')
        print(response['MessageId'])
        
    return 'hellofrom s3trigger'

