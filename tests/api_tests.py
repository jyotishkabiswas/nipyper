import unittest
from unittest import TestCase
import requests

class APITest(TestCase):

    def test_run_post_interface(self):
        url = "http://localhost:5000/workflows/test"

        payload = "{\n    'name': 'test_fn',\n    'type': 'Interface',\n    'interface': 'utility.Function',\n    'keywords': {\n        'input_names': ['a', 'b'],\n        'output_names': ['out']\n    },\n    'inputs': {\n        'function_str': 'def _add(a, b):\\n    return a + b',\n        'a': 5,\n        'b': 7\n    }\n}"
        headers = {
            'content-type': "application/json",
            'cache-control': "no-cache",
            'postman-token': "1c602522-9237-213a-e7a8-9bc6353f2fc7"
            }

        response = requests.request("POST", url, data=payload, headers=headers)

        print(response.text)

if __name__ == '__main__':
    unittest.main()