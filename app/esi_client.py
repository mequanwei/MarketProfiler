import requests
from typing import Dict, Any
import base64
import random
import requests
import string
import urllib
import sqlite3
import time

import jwt

client_id = "acdd73ce088d436ba3edf469e099ecae"
client_secret = "alOhr3hpwWhb7Pu4P3YSvps4Vaxc7E9Vk4VKzGG3"

class ESIClient:
    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')  # 移除末尾斜杠以避免重复
        self.headers = headers or {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.token = {}
    
    def get(self, endpoint: str, params: Dict[str, Any] = None,access_token: str = None) -> Dict[str, Any]:
        """发送 GET 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        if access_token:
            headers['Authorization'] = f"Bearer {access_token}"
        response = self.session.get(url, params=params,headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any] = None, json_data: Dict[str, Any] = None,access_token: str = None) -> Dict[str, Any]:
        """发送 POST 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        if access_token:
            headers['Authorization'] = f"Bearer {access_token}"

        response = self.session.post(url, data=data, json=json_data,headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()


    def redirect_to_sso(self,scopes, redirect_uri):
        """
        Generates a URL to redirect the user to the SSO for authentication.

        :param list[str] scopes: A list of scopes that the application is requesting access to
        :param str redirect_uri: The URL where the user will be redirected back to after the authorization flow is complete
        :returns: A tuple containing the URL and the state parameter that was used
        """
        state = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        query_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
        }
        query_string = urllib.parse.urlencode(query_params)
        return (f"https://login.eveonline.com/v2/oauth/authorize?{query_string}", state)
    
    def request_token(self,authorization_code):
        """
        Takes an authorization code and exchanges it for an access token and refresh token.

        :param str authorization_code: The authorization code received from the SSO
        :returns: A dictionary containing the access token and refresh token
        """
        basic_auth = base64.urlsafe_b64encode(
            f"{client_id}:{client_secret}".encode("utf-8")
        ).decode()
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "authorization_code",
            "code": authorization_code,
        }
        response = requests.post(
            "https://login.eveonline.com/v2/oauth/token", headers=headers, data=payload
        )
        response.raise_for_status()

        return response.json()
    
    def refresh_token(self,token):
        """
        Takes a refresh token and exchanges it for a new access token and refresh token.

        :param str refresh_token: The refresh token received from the SSO
        :returns: A dictionary containing the new access token and refresh token
        """
        basic_auth = base64.urlsafe_b64encode(
            f"{client_id}:{client_secret}".encode("utf-8")
        ).decode()
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": token,
        }
        response = requests.post(
            "https://login.eveonline.com/v2/oauth/token", headers=headers, data=payload
        )
        response.raise_for_status()

        return response.json()

    def fetch_jwks_metadata(self):
        """
        Fetches the JWKS metadata from the SSO server.

        :returns: The JWKS metadata
        """
        METADATA_URL = "https://login.eveonline.com/.well-known/oauth-authorization-server"
        global jwks_metadata, jwks_metadata_ttl
        if jwks_metadata is None or jwks_metadata_ttl < time.time():
            resp = requests.get(METADATA_URL)
            resp.raise_for_status()
            metadata = resp.json()

            jwks_uri = metadata["jwks_uri"]
            #https://login.eveonline.com/oauth/jwks

            resp = requests.get(jwks_uri)
            resp.raise_for_status()

            jwks_metadata = resp.json()
        return jwks_metadata["keys"]


    def validate_jwt_token(self,token):
        """
        Validates a JWT Token.

        :param str token: The JWT token to validate
        :returns: The content of the validated JWT access token
        :raises ExpiredSignatureError: If the token has expired
        :raises JWTError: If the token is invalid
        """
        keys = self.fetch_jwks_metadata()
        # keys= [
        #     {
        #     "alg": "RS256",
        #     "e": "AQAB",
        #     "kid": "JWT-Signature-Key",
        #     "kty": "RSA",
        #     "n": "nehPQ7FQ1YK-leKyIg-aACZaT-DbTL5V1XpXghtLX_bEC-fwxhdE_4yQKDF6cA-V4c-5kh8wMZbfYw5xxgM9DynhMkVrmQFyYB3QMZwydr922UWs3kLz-nO6vi0ldCn-ffM9odUPRHv9UbhM5bB4SZtCrpr9hWQgJ3FjzWO2KosGQ8acLxLtDQfU_lq0OGzoj_oWwUKaN_OVfu80zGTH7mxVeGMJqWXABKd52ByvYZn3wL_hG60DfDWGV_xfLlHMt_WoKZmrXT4V3BCBmbitJ6lda3oNdNeHUh486iqaL43bMR2K4TzrspGMRUYXcudUQ9TycBQBrUlT85NRY9TeOw",
        #     "use": "sig"
        #     },
        #     {
        #     "alg": "ES256",
        #     "crv": "P-256",
        #     "kid": "8878a23f-2489-4045-989e-4d2f3ec1ae1a",
        #     "kty": "EC",
        #     "use": "sig",
        #     "x": "PatzB2HJzZOzmqQyYpQYqn3SAXoVYWrZKmMgJnfK94I",
        #     "y": "qDb1kUd13fRTN2UNmcgSoQoyqeF_C1MsFlY_a87csnY"
        #     }
        # ]
        # Fetch the key algorithm and key idfentifier from the token header
        header = jwt.get_unverified_header(token)
        key = [
            item
            for item in keys
            if item["kid"] == header["kid"] and item["alg"] == header["alg"]
        ].pop()
        ACCEPTED_ISSUERS = ("logineveonline.com", "https://login.eveonline.com")
        EXPECTED_AUDIENCE = "EVE Online"
        contents = jwt.decode(
            token=token,
            key=key,
            algorithms=key["alg"],
            issuer=ACCEPTED_ISSUERS,
            audience=EXPECTED_AUDIENCE,
            )
        
        return contents
        

    def is_token_valid(self,token):
        """
        Simple check if the token is valid or not.

        :returns: True if the token is valid, False otherwise
        """
        
        claims = self.validate_jwt_token(token)
        # If our client_id is in the audience list, the token is valid, otherwise, we got a token for another client.
        return client_id in claims["aud"]
        

    def get_charcter_info(slef,token):
        info = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        name = info['name']
        character_id = info["sub"].split(":")[-1]
        return name,character_id
            
    def get_system_id(self):
        return self.get('/universe/systems/')
    
    def get_system_info(self,id):
        return self.get(f'/universe/systems/{id}/')
    
    def get_industry_index(self):
        return self.get('/industry/systems/')
    


    def get_wallet(self,c_id,token):
        return self.get(f'/characters/{c_id}/wallet/',access_token=token)
    
    def get_jobs(self,c_id,token):
        return self.get(f'/characters/{c_id}/industry/jobs/',access_token=token)
        
    
    

    def close(self):
        """关闭会话"""
        self.session.close()