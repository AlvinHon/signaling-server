import boto3
from boto3.dynamodb.conditions import Attr
import uuid
import simplejson as json
import time

dynamodb = boto3.resource('dynamodb')
data_channel = dynamodb.Table('data-channel')

def lambda_handler(event, context):
    rpc, err_msg = validate_rpc(event)
    if rpc is None:
        return error_response(err_msg)
    
    rpc_method = rpc['method']
    match str(rpc_method):
        case 'create_data_channel':
            return handle_create_data_channel()
        case 'create_offer':
            return handle_create_offer(rpc)
        case 'get_offer':
            return handle_get_offer(rpc)
        case 'create_candidate':
            return handle_create_candidate(rpc)
        case 'create_answer':
            return handle_create_answer(rpc)
        case 'get_candidates':
            return handle_get_candidates(rpc)
        case 'get_answer':
            return handle_get_answer(rpc)
        case 'echo': # for testing purpose
            return handle_echo(rpc)
        case _:
            return error_response("unknown method " + rpc_method)

def handle_create_data_channel():
    # generate random channel id
    channel_id = str(uuid.uuid4())
    # get utc timestamp + 5 minutes
    expire_time = int(time.time()) + 300
    try:
        data_channel.put_item(
            Item={
                'channel_id': channel_id,
                'expire_time': expire_time,
            },
            ConditionExpression=Attr('channel_id').not_exists(),
        )
    except:
        return error_response('try again!')
    
    return ok_response({ 'channel_id': channel_id })

def handle_create_offer(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    if 'offer' not in rpc:
        return error_response('offer is required')
    
    channel_id = rpc['channel_id']
    offer = rpc['offer']

    try:
        data_channel.update_item(
            Key={
                'channel_id': channel_id,
            },
            UpdateExpression='SET offer = :offer',
            ExpressionAttributeValues={
                ':offer': str(offer),
            },
        )
    except:
        return error_response('fail to create offer')

    return ok_response()

def handle_get_offer(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    
    channel_id = rpc['channel_id']

    response = data_channel.get_item(
        Key={
            'channel_id': channel_id,
        },
    )

    if 'Item' not in response:
        return error_response('channel_id not found')
    
    if 'offer' not in response['Item']:
        return error_response('offer not found')

    return ok_response({ 'offer': response['Item']['offer'] })

def handle_create_candidate(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    if 'candidate' not in rpc:
        return error_response('candidate is required')
    
    channel_id = rpc['channel_id']
    candidate = rpc['candidate']

    try:
        data_channel.update_item(
            Key={
                'channel_id': channel_id,
            },
            UpdateExpression='SET candidate = list_append(if_not_exists(candidate, :empty_list), :candidate)',
            ExpressionAttributeValues={
                ':candidate': [candidate],
                ':empty_list': [],
            },
        )
    except:
        return error_response('fail to create candidate')

    return ok_response()

def handle_create_answer(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    if 'answer' not in rpc:
        return error_response('answer is required')
    
    channel_id = rpc['channel_id']
    answer = rpc['answer']

    # update only if answer is not exist
    try:
        data_channel.update_item(
            Key={
                'channel_id': channel_id,
            },
            UpdateExpression='SET answer = :answer',
            ConditionExpression=Attr('answer').not_exists(),
            ExpressionAttributeValues={
                ':answer': str(answer),
            },
            ReturnValues='NONE',
            ReturnConsumedCapacity='NONE',
            ReturnItemCollectionMetrics='NONE',
            ReturnValuesOnConditionCheckFailure='NONE',
        )
        
        return ok_response()
    except data_channel.meta.client.exceptions.ConditionalCheckFailedException:
        return error_response('answer already exist')
    except:
        return error_response('fail to create answer')

def handle_get_candidates(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    
    channel_id = rpc['channel_id']

    response = data_channel.get_item(
        Key={
            'channel_id': channel_id,
        },
    )

    if 'Item' not in response:
        return error_response('channel_id not found')
    
    if 'candidate' not in response['Item']:
        return ok_response({ 'items': [] })

    return ok_response({ 'items': response['Item']['candidate'] })

def handle_get_answer(rpc):
    if 'channel_id' not in rpc:
        return error_response('channel_id is required')
    
    channel_id = rpc['channel_id']

    response = data_channel.get_item(
        Key={
            'channel_id': channel_id,
        },
    )

    if 'Item' not in response:
        return error_response('channel_id not found')
    
    if 'answer' not in response['Item']:
        return error_response('answer not found')

    return ok_response({ 'answer': response['Item']['answer'] })

def handle_echo(rpc):
    return ok_response(rpc)

def validate_rpc(event):
    if 'requestContext' not in event:
        return None, 'Not a valid request'
    if 'http' not in event['requestContext']:
        return None, 'Not a valid request'
    if 'method' not in event['requestContext']['http']:
        return None, 'Not a valid request'
    if event['requestContext']['http']['method'] != 'POST':
        return None, 'Only accept POST method'
    
    rpc = json.loads(event['body'])
    if 'method' not in rpc:
        return None, 'Not a valid rpc. HTTP post body must be a json object with method key'
    return rpc, ''

def error_response(message=''):
    return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': message,
    }

def ok_response(body=''):
    headers_type = 'text/plain'
    if type(body) == dict:
        body = json.dumps(body)
        headers_type = 'application/json'
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': headers_type
        },
        'body': body,
    }