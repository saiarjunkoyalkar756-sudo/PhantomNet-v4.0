import json
import unittest
from backend_api.log_parsers.aws_cloudtrail_parser import AWSCloudTrailParser

class TestAWSCloudTrailParser(unittest.TestCase):

    def setUp(self):
        self.parser = AWSCloudTrailParser()
        self.sample_cloudtrail_log = """
        {
            "eventVersion": "1.08",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": "AIDAJ45Q7YFFAWEXAMPLE",
                "arn": "arn:aws:iam::123456789012:user/test-user",
                "accountId": "123456789012",
                "accessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "userName": "test-user"
            },
            "eventTime": "2023-11-29T10:00:00Z",
            "eventSource": "s3.amazonaws.com",
            "eventName": "GetObject",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "192.0.2.1",
            "userAgent": "S3-SDK-For-Go/1.44.133 (go1.18.1; linux; amd64)",
            "requestParameters": {
                "bucketName": "my-test-bucket",
                "key": "test-object.txt"
            },
            "responseElements": null,
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "test-config-id",
                "bucket": {
                    "name": "my-test-bucket",
                    "ownerIdentity": {
                        "principalId": "A3S5R8EXAMPLE"
                    },
                    "arn": "arn:aws:s3:::my-test-bucket"
                },
                "object": {
                    "key": "test-object.txt",
                    "size": 1024,
                    "eTag": "d41d8cd98f00b204e9800998ecf8427e",
                    "sequencer": "005E5D5A5C5D5E5D5"
                }
            }
        }
        """

    def test_parse_valid_cloudtrail_log(self):
        parsed_data, raw_log = self.parser.parse(self.sample_cloudtrail_log)
        
        # Check that the raw log is returned correctly
        self.assertEqual(raw_log, self.sample_cloudtrail_log)
        
        # Check that the parsed data is a dictionary
        self.assertIsInstance(parsed_data, dict)
        
        # Check for some key fields to ensure it was parsed correctly
        self.assertEqual(parsed_data["eventSource"], "s3.amazonaws.com")
        self.assertEqual(parsed_data["eventName"], "GetObject")
        self.assertEqual(parsed_data["userIdentity"]["userName"], "test-user")
        self.assertEqual(parsed_data["requestParameters"]["bucketName"], "my-test-bucket")

    def test_parse_invalid_json(self):
        invalid_log = "This is not a valid JSON string"
        parsed_data, raw_log = self.parser.parse(invalid_log)
        
        # For invalid JSON, we expect an empty dictionary
        self.assertEqual(parsed_data, {})
        self.assertEqual(raw_log, invalid_log)

if __name__ == '__main__':
    unittest.main()
