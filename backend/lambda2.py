from __future__ import print_function
import boto3
import json
import argparse
import pprint
from botocore.vendored import requests #lambda do not have requests module
import sys
import urllib
import logging
import ast
from boto3 import resource

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

API_KEY= 
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'
SEARCH_LIMIT = 3

def request(host, path, api_key, url_params=None):
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    url_params = url_params or {}
	#url = '{0}{1}'.format(host, quote(path.encode('utf8')))

    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()

    #return response.json()

# def search(api_key, term, location):
# 	url_params = {
#         'term': term.replace(' ', '+'),
#         'location': location.replace(' ', '+'),
#         'limit': SEARCH_LIMIT
#     }
#     return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)
#     #return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def get_business(api_key, business_id):

    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)

def search(api_key, term, location):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def query_api(term, location):

    response = search(API_KEY, term, location)

    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return None

    business_id = businesses[0]['id']

    print(u'{0} businesses found, querying business info ' \
        'for the top result "{1}" ...'.format(
            len(businesses), business_id))
    response = get_business(API_KEY, business_id)

    print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)
    return response

def lambda_handler(event, context):

    sqs = boto3.client('sqs')

    queue_url = 'https://sqs.us-east-1.amazonaws.com/330744403812/RestaurantRequest'

    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    #logging.info(response)
    print(response)

    try:

        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']

        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print('Received and deleted message: %s' % message)

        DEFAULT_TERM = ast.literal_eval(message[unicode('Body')])['Cuisine']#message is a dict, message[unicode('Body')] is a String of dict.
        DEFAULT_LOCATION = ast.literal_eval(message[unicode('Body')])['Location']
        user_phone_number = ast.literal_eval(message[unicode('Body')])['PhoneNumber']
        dining_date = ast.literal_eval(message[unicode('Body')])['date']
        dining_time = ast.literal_eval(message[unicode('Body')])['time']
        number_people = ast.literal_eval(message[unicode('Body')])['NumberOfPeople']



        parser = argparse.ArgumentParser()

        parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
                            type=str, help='Search term (default: %(default)s)')
        parser.add_argument('-l', '--location', dest='location',
                            default=DEFAULT_LOCATION, type=str,
                            help='Search location (default: %(default)s)')

        input_values = parser.parse_args()

        try:

            query_result = query_api(input_values.term, input_values.location)
            print('queryMessage from sqs:')
            pprint.pprint(query_result, indent=2)

        except HTTPError as error:
            sys.exit(
                'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                    error.code,
                    error.url,
                    error.read(),
                )
            )

        restaurant_id = query_result[unicode('id')]
        #print(restaurant_id)
        restaurant_name = query_result[unicode('name')]
        #print(restaurant_name)
        restaurant_phone_num = query_result[unicode('phone')]
        #print(restaurant_phone_num)
        restaurant_location = query_result[unicode('location')][unicode('display_address')][0]+unicode(', ')+query_result[unicode('location')][unicode('display_address')][1]
        #print(restaurant_location)
        restaurant_url = query_result[unicode('url')]

        dynamodb_resource = resource('dynamodb')
        table = dynamodb_resource.Table('restaurants')
        response = table.put_item(Item={
            'id':restaurant_id,
            'name':restaurant_name,
            'location': restaurant_location,
            'phone number':restaurant_phone_num
            })

        #=========send message from aws SMS============#
        sendMessage = 'Hello! Here is the {} restaurant suggestion for {} people, for {} at {}: Name: {}; Location: {};.Enjoy your meal!'.format(DEFAULT_TERM, number_people, dining_date, dining_time, restaurant_name, restaurant_location)

        print('sent message: '+ sendMessage)


        sns = boto3.client('sns')
        sns.publish(
           PhoneNumber = '+1'+unicode(user_phone_number),
           # PhoneNumber = '+16462677411',
           Message = sendMessage
        )
    except:
        message = "No record"

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')

    }
