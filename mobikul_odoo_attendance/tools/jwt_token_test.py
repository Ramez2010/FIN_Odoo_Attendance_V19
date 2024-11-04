# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import unittest
import jwt_token
from jwt.exceptions import DecodeError

class Tests(unittest.TestCase):

    def test_empty_payload(self):
        test_data = {"payload":{},
        "secret": "abc",
        "algorithm": "HS256"
        ""
        }
        required_result = [b'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.e30.Xu_sWESYaAuv0WOxMPW53WA8nNsmPEylF__ce_NE3L4',\
        b'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.yYhP2xosmpuyV5aoT8mz7GFESzq3hKSy-CRWC-vYOIU']
        self.assertIn(jwt_token.jwt_encode(test_data["payload"], test_data["secret"], test_data["algorithm"]), \
        required_result)


    def test_algorithm_absent(self):
        test_data = {"payload":{
          "sub": "1234567890",
          "name": "John Doe",
          "iat": 1516239022
        },
        "secret": "abc",
        "algorithm": ""
        ""
        }
        with self.assertRaises(NotImplementedError):
            jwt_token.jwt_encode(test_data["payload"], test_data["secret"], test_data["algorithm"])


    def test_wrong_secret_at_decode(self):
        test_data = {"payload":{
          "sub": "1234567890",
          "name": "John Doe",
          "iat": 1516239022
        },
        "secret": "abc",
        "algorithm": "HS256"
        ""
        }
        token = jwt_token.jwt_encode(test_data["payload"], test_data["secret"], test_data["algorithm"])
        with self.assertRaises(DecodeError):
            jwt_token.jwt_decode(token, "ab", test_data["algorithm"])


    def test_wrong_token_at_decode(self):
        test_data = {"payload":{
          "sub": "1234567890",
          "name": "John Doe",
          "iat": 1516239022
        },
        "secret": "abc",
        "algorithm": "HS256"
        ""
        }
        token = jwt_token.jwt_encode(test_data["payload"], test_data["secret"], test_data["algorithm"])
        with self.assertRaises(DecodeError):
            jwt_token.jwt_decode("eyJhbGciOiJIUzI1NiIsIn6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "ab", test_data["algorithm"])

if __name__ == "__main__":
    unittest.main()
