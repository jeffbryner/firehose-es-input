# firehose-es-input
Mimic an ES endpoint to accept json events from things that would usually post to an elastic search _bulk endpoint and send them to AWS firehose

## Why
Tools like filebeat and others are great for shipping logs/events into centralized log systems. The open ES protocol is commonly used for talking to the API providing a _bulk endpoint for posting events from log shippers. Taking that and converting the request to firehose can offer an easy way to integrate to AWS and land in a number of destinations.


### installation
- npm install --save-dev serverless
- sls plugin install -n serverless-wsgi
- sls plugin install -n serverless-python-requirements


### lambda configuration
The program expects a config.yml file with the following settings:

```yaml
ENVIRONMENT: dev
REGION: us-west-2
FIREHOSE_DELIVERY_STREAM: data_lake_s3_stream
API_KEY: api_key_goes_here
```

The API_KEY is optional, but strongly encouraged if you are exposing this on the open internet. The other settings are likely self-explanatory.

The configuration logic will look first to config.yml for default, then config.dev|prod.yml if you've set an env variable called ENVIRONMENT to something. Lastly it will read in the OS environment to allow for any overrides using environment variables.

This should allow you to configure for defaults, dev, test, prod and lambda deployments.

You will need an ES license (from eshost:9200/_license) placed in license.json.


### lambda deployment
Using the serverless framework deploy via a:

```bash
sls deploy  # for development
sls deploy --stage prod # for production
```

you should have a config.env.yml (i.e. config.dev.yml, config.prod.yml) for each environment you plan to support. The serverless.yml config looks for these to set IAM roles, etc.


### libbeat configuration
As an example shipper configuration you can setup filebeat to talk to this endpoint by setting this stanza appropriately:

```yaml
# ---------------------------- Elasticsearch Output ----------------------------
output.elasticsearch:
  # Array of hosts to connect to.
  hosts: ["n<apigipperish>g.execute-api.us-west-2.amazonaws.com:443/dev/"]
  #hosts: ["localhost:5000"]

  # Protocol - either `http` (default) or `https`.
  protocol: "https"

  # Authentication credentials - either API key or username/password.
  api_key: "id:api_key_goes_here"

```

If you are deploying/testing locally, localhost will do. If you deploy this lambda you will get the api gateway address and can use that as shown above to configure (note the /dev/ or /prod/ in the url for the gateway depending on how you've deployed it.)

