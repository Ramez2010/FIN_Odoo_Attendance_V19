# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import jwt

def jwt_encode(payload, secret, algorithm):
    """
    Create the JWT token

    :payload : dict
    :secret : string
    :algorithm : string

    :return: string
    """
    encoded_jwt = jwt.encode(payload, secret, algorithm)
    return encoded_jwt

def jwt_decode(jwt_token, secret, algorithm):
    """
    Decode the JWT token and provide the test_empty_payload

    :payload : string
    :secret : string
    :algorithm : string

    :return: dict
    """
    if not secret:
        secret = "dummySecretKey"
    payload = jwt.decode(jwt_token, secret, algorithm)

    return payload

# if __name__ == "__main__":
#     payload = {
#       "sub": "1234567890",
#       "name": "John Doe",
#       "iat": 1516239022
#     }
#     secret = "abc"
#     algorithm = "HS256"
#     token = jwt_encode(payload, secret, algorithm)
#     print(token)
#     print()
#     decode_secret = "abc"
#     payload = jwt_decode(token, decode_secret, "")
#     print(payload)
