import unittest
import mock

from program import environment_configured


@mock.patch('program.logging')
class Tests(unittest.TestCase):

    @mock.patch.dict('os.environ', {"bucket_name": "bucket"})
    @mock.patch.dict('os.environ', {"aws_access_key_id": "id"})
    @mock.patch.dict('os.environ', {"aws_secret_access_key": "secret"})
    def test_returns_true_when_everything_is_set(self, mock_logging):
        self.assertTrue(environment_configured())
        mock_logging.error.assert_not_called()

    @mock.patch.dict('os.environ', {"aws_access_key_id": "id"})
    @mock.patch.dict('os.environ', {"aws_secret_access_key": "secret"})
    def test_returns_false_when_bucket_name_is_missing(self, mock_logging):
        self.assertFalse(environment_configured())
        mock_logging.error.assert_called_once_with('bucket_name is not set')

    @mock.patch.dict('os.environ', {"bucket_name": "bucket"})
    @mock.patch.dict('os.environ', {"aws_secret_access_key": "secret"})
    def test_returns_false_when_aws_access_key_id_is_missing(self, mock_logging):
        self.assertFalse(environment_configured())
        mock_logging.error.assert_called_once_with('aws_key is not set')

    @mock.patch.dict('os.environ', {"bucket_name": "bucket"})
    @mock.patch.dict('os.environ', {"aws_access_key_id": "id"})
    def test_returns_false_when_aws_secret_access_key_is_missing(self, mock_logging):
        self.assertFalse(environment_configured())
        mock_logging.error.assert_called_once_with('aws_secret is not set')
