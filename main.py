import program
import logging
import uuid
import json

logging.basicConfig(level=logging.INFO)

test_event_body = json.dumps({'tickets_to_return': 5})
test_event = {'body': test_event_body}
test_context = type('obj', (object,), {'aws_request_id': str(uuid.uuid4())})()

print(program.lambda_handler(test_event, test_context))
