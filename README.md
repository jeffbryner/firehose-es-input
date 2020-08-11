# firehose-es-input
Mimic an ES endpoint to accept json events from things that would usually post to an elastic search _bulk endpoint and send them to AWS firehose

## Why
Tools like filebeat and others are great for shipping logs/events into centralized log systems. They use the open ES protocol for talking to the API. We can expand the range of destinations by doing a transformation from a normal ES _bulk request to firehose to land in a number of destinations.


### installation
- npm install --save-dev serverless
- npm install --save-dev serverless-apigw-binary ?
- npm install --save-dev serverless-python-requirements
- npm install --save-dev serverless-wsgi

###
