import datetime
import hashlib
import hmac
import requests
import boto3
import json
from urllib import parse

class APIManager(object):
    def __init__(self, host, stage, api_key):
        self.host = host
        self.stage = stage
        self.api_key = api_key

        config = requests.get("https://{host}/{stage}/".format(host=host, stage=stage),
                              headers={'x-api-key': api_key}).json()
        self.region = config['Region']
        self.identity_pool_id = config['IdentityPoolId']

    def get_federation_credentials(self, provider, token):
        print(provider, token)
        client_identity = boto3.client('cognito-identity', self.region)
        fed_id = client_identity.get_id(IdentityPoolId=self.identity_pool_id, Logins={provider: token})
        credentials = client_identity.get_credentials_for_identity(
            IdentityId=fed_id['IdentityId'],                                                            Logins={provider: token})
        return credentials['Credentials']

    def post_events(self, provider, token, payload):
        method = 'POST'
        payload_str = json.dumps(payload)
        credentials = self.get_federation_credentials(provider,token)
        request_url, headers = self._generate_signed_request(method,'events',credentials, payload=payload_str)

        response = requests.request(method, request_url, headers=headers, json=payload)
        if response.status_code != 200:
            print('Response reason: ' + response.reason)
            print('Response headers: {}'.format(response.headers))
            print('Response content: ' + str(response.content))
            raise ValueError() # TODO better error handling
        return response.json()

    def get_testdata(self, provider, token, **parameters):

        parameters_str = parse.urlencode(parameters)
        credentials = self.get_federation_credentials(provider,token)
        request_url, headers = self._generate_signed_request('GET','testdata',credentials,request_parameters=parameters_str)

        response = requests.get(request_url, headers=headers)
        if response.status_code != 200:
            print('Response reason: ' + response.reason)
            print('Response headers: {}'.format(response.headers))
            print('Response content: ' + str(response.content))
            raise ValueError() # TODO better error handling
        return response.json()


    def _generate_signed_request(self, http_method, method, credentials,
                                 payload="", request_parameters=""):
        service = 'execute-api'
        keypath = '/{stage}/{method}'.format(stage=self.stage, method=method)
        # Create a date for headers and the credential string
        t = datetime.datetime.utcnow()
        amzdate = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

        # Key derivation functions. See:
        # http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

        def getSignatureKey(key, dateStamp, regionName, serviceName):
            kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
            kRegion = sign(kDate, regionName)
            kService = sign(kRegion, serviceName)
            kSigning = sign(kService, 'aws4_request')
            return kSigning

        # ************* TASK 1: CREATE A CANONICAL REQUEST *************
        # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        canonical_headers = 'host:' + self.host + '\n' + 'x-amz-date:' + amzdate + '\n'
        signed_header_keys = 'host;x-amz-date'

        # Create payload hash (hash of the request body content). For GET
        # requests, the payload is an empty string ("").
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

        # Combine elements to create create canonical request
        canonical_request = http_method + '\n' + keypath + '\n' + request_parameters + '\n' + canonical_headers + '\n' + signed_header_keys + '\n' + payload_hash

        # ************* TASK 2: CREATE THE STRING TO SIGN*************
        # Match the algorithm to the hashing algorithm you use, either SHA-1 or
        # SHA-256 (recommended)
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = datestamp + '/' + self.region + '/' + service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' \
                         + amzdate + '\n' \
                         + credential_scope \
                         + '\n' \
                         + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

        # ************* TASK 3: CALCULATE THE SIGNATURE *************
        # Create the signing key using the function defined above.
        signing_key = getSignatureKey(credentials['SecretKey'], datestamp, self.region, service)

        # Sign the string_to_sign using the signing_key
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

        # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
        # The signing information can be either in a query string value or in
        # a header named Authorization. This code shows how to use a header.
        # Create authorization header and add to request headers
        authorization_header = algorithm + ' ' \
                               + 'Credential=' + credentials['AccessKeyId'] + '/' + credential_scope + ', ' \
                               + 'SignedHeaders=' + signed_header_keys + ', ' \
                               + 'Signature=' + signature

        # The request can include any headers, but MUST include "host", "x-amz-date",
        # and (for this scenario) "Authorization". "host" and "x-amz-date" must
        # be included in the canonical_headers and signed_headers, as noted
        # earlier. Order here is not significant.
        # Python note: The 'host' header is added automatically by the Python 'requests' library.
        signed_headers = {'x-amz-date': amzdate,
                          'Authorization': authorization_header,
                          'x-api-key': self.api_key,
                          'x-amz-security-token': credentials['SessionToken']}

        request_url = 'https://{}{}?{}'.format(self.host, keypath, request_parameters)

        return request_url, signed_headers