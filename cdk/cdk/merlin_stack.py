from collections.abc import Mapping

from aws_cdk import Stack
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_dynamodb import TableV2, Attribute, AttributeType

from constructs import Construct

VERSION = '2'

class MerlinStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self._bucket = self._get_bucket()

        self._db = self._create_db()
        self._create_postMessage()

    def _get_bucket(self) -> Bucket:
        return Bucket.from_bucket_attributes(self, "Bucket",
            bucket_arn='arn:aws:s3:::merlin-1758dca1a93843f1a03d0b6d8f9277d1',
        )

    def _create_db(self) -> TableV2:
        return TableV2(self, "messages",
            partition_key=Attribute(
                name="game",
                type=AttributeType.STRING,
            ),
            sort_key=Attribute(
                name="seq",
                type=AttributeType.NUMBER,
            ),
        )

    def _create_postMessage(self) -> Function:
        function = self._create_postMessage_function()
        self._db.grant_read_write_data(function)
        return function

    def _create_postMessage_function(self) -> Function:
        return Function(self, "postMessage",
            runtime = Runtime.PYTHON_3_12,
            handler = 'postMessage.lambda_handler',
            code = self._postMessage_code(),
            environment=self._lambda_environment(),
        )

    def _postMessage_code(self) -> Code:
        return Code.from_bucket_v2(
            self._bucket,
            f'dist/lambda/postMessages/versions/{VERSION}/lambda.zip',
        )

    def _lambda_environment(self) -> Mapping[str, str]:
        return {
            'MESSAGES_TABLE': self._db.table_name,
        }
