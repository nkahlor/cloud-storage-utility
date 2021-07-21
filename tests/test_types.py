import unittest

from cloud_storage_utility.types.bucket_key import BucketKeyMetadata


class TestTypes(unittest.TestCase):
    def test_bucket_metadata(self):
        metadata = BucketKeyMetadata(last_modified="2021-07-18T20:15:01.439Z", bytes=5)
        self.assertEqual(metadata.bytes, int(metadata.bytes))

        metadata = BucketKeyMetadata(last_modified="2021-07-18T20:15:01.439Z", bytes="5")
        self.assertNotEqual(metadata.bytes, int(metadata.bytes))

if __name__ == '__main__':
    unittest.main()
