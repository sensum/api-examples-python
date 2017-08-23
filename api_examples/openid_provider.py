import boto3
from warrant import AWSSRP


def get_cognito_provider_token(username:str, password:str, region:str,
                               pool_id:str='eu-west-1_CQvokDu8q',
                               app_id:str='5fphra1ppjstegp0rlcfrgi6mn'):
    """
    Authenticate with Cognito Identity Provider using the provided credentials
    and return the OpenID Connect Provider ID and Token

    :param username:
    :param password:
    :param region: AWS Service region
    :param pool_id: Cognito User Pool ID from Cognito Identity Provider
    :param app_id: Cognito User Pool Client App ID
    :return: provider, token
    :rtype: str, str
    """
    # Client Id from Cognito Identity Provider
    client_idp = boto3.client('cognito-idp')
    aws = AWSSRP(username=username, password=password, pool_id=pool_id,
                 client_id=app_id, client=client_idp)
    tokens = aws.authenticate_user()
    # A valid provider string for cognito is generated below, ready to be
    # passed on to the main federation credentials functionality in
    # `api_auth`
    provider = 'cognito-idp.{}.amazonaws.com/{}'.format(region, pool_id)
    token = tokens['AuthenticationResult']['IdToken']
    return provider, token