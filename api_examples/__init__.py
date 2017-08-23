import json
import os

from sensumapi import APIManager
from sensumapi.openid_provider import get_cognito_provider_token

def main():
    api_key = 'PublicDemoKeyForDocumentation'
    host = 'api.sensum.co'
    stage = 'v0'

    # Secondary authentication information such as the AWS connectivity region and
    # identity pool are provided at the base of the endpoint to valid api keys


    # In this example,

    username = 'testuser'
    password = 'testPassword1!'
    cognito_pool_id = os.environ.get('COGNITO_POOL_ID', None)
    cognito_app_id = os.environ.get('COGNITO_APP_ID', None)
    cognito_region = 'eu-west-1' #NOT NECESSARILY THE SAME AS THE FED REGION
    provider, token = get_cognito_provider_token(username, password, cognito_region, cognito_pool_id, cognito_app_id)

    print(provider, token)

    mgr = APIManager(host,stage,api_key)

    response = mgr.get_testdata(provider, token)

    print(json.dumps(response, indent=2))

    response = mgr.post_events(provider, token, response['data'])

    print(json.dumps(response, indent=2))



    # request_url, headers = generate_signed_request('POST', 'events', credentials['Credentials'], api_key,
    #                                                payload=json.dumps(body))
    #
    # print('\nBEGIN REQUEST++++++++++++++++++++++++++++++++++++')
    # print('Request URL = ' + request_url)
    # print(json.dumps(headers, indent=2))
    # r = requests.post(request_url, headers=headers, json=body)
    #
    # print('\nRESPONSE++++++++++++++++++++++++++++++++++++')
    # print('Response code: %d\n' % r.status_code)
    # try:
    #     response = r.json()
    #     body = response['data']
    #     print(body)
    # except:
    #     print('Response reason: ' + r.reason)
    #     print('Response headers: {}'.format(r.headers))
    #     print('Response content: ' + str(r.content))
    #     body = response


if __name__ == '__main__':
    main()
