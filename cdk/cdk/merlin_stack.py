from collections.abc import Mapping
from inspect import cleandoc

from aws_cdk import Stack
from aws_cdk.aws_apigateway import RestApi, Resource, Method, Integration, LambdaIntegration, PassthroughBehavior
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_dynamodb import TableV2, Attribute, AttributeType

from constructs import Construct

API_VERSION = '2'

class MerlinStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self._bucket = self._get_bucket()

        self._db = self._create_db()
        self._create_lambdas()
        self._create_api()

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

    def _create_lambdas(self):
        self._create_postMessage()
        self._getMessages_lambda = self._create_getMessages()

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
            f'dist/lambda/postMessages/versions/{API_VERSION}/lambda.zip',
        )

    def _create_getMessages(self) -> Function:
        function = self._create_getMessages_function()
        self._db.grant_read_data(function)
        return function

    def _create_getMessages_function(self) -> Function:
        return Function(self, "getMessages",
            runtime = Runtime.PYTHON_3_12,
            handler = 'getMessages.lambda_handler',
            code = self._getMessages_code(),
            environment=self._lambda_environment(),
        )

    def _getMessages_code(self) -> Code:
        return Code.from_bucket_v2(
            self._bucket,
            f'dist/lambda/getMessages/versions/{API_VERSION}/lambda.zip',
        )

    def _lambda_environment(self) -> Mapping[str, str]:
        return {
            'MESSAGES_TABLE': self._db.table_name,
        }

    def _create_api(self) -> RestApi:
        api = RestApi(self, "Api",
        )
        api_resource = api.root.add_resource('api')
        v1_resource = api_resource.add_resource('v1')
        game_resource = v1_resource.add_resource('{game}')
        messages_resource = game_resource.add_resource('messages')
        self._create_messages_get(messages_resource)
        self._create_messages_post(messages_resource)

    def _create_messages_get(self, messages_resource: Resource) -> Method:
        return messages_resource.add_method("GET",
            integration = self._messages_get_integration(),
            request_parameters = {
                'method.request.path.game' : True,
                'method.request.querystring.start' : False,
                'method.request.querystring.end' : False,
            },
        )

    def _messages_get_integration(self) -> Integration:
        return LambdaIntegration(
            self._getMessages_lambda,
            proxy = False,
            passthrough_behavior = PassthroughBehavior.NEVER,
            request_parameters = {
                'integration.request.path.game': 'method.request.path.game',
                'integration.request.querystring.start': 'method.request.querystring.start',
                'integration.request.querystring.end': 'method.request.querystring.end',
            },
            request_templates = {
                'application/json': cleandoc('''
                    {
                        "game": "$input.params('game')",
                        "start": "$input.params('start')",
                        "end": "$input.params('end')"
                    }
                '''),
            }
        )

    def _create_messages_post(self, messages_resource: Resource) -> Method:
        return messages_resource.add_method("POST",
        )
