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
API_KEY: base64_of_id:api_key_goes_here
USERNAME: username
PASSWORD: password
```
Leave values blank for none/unsupported.

If you don't set either API_KEY or USERNAME/PASSWORD there will be no authentication which is NOT RECOMMENDED as it could allow someone to inject data into your environment.

API keys have an ID and Value base64 encoded as [id:value](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-api-create-api-key.html)

The value expected here is the base64 encoded combination of id:value

Enabling either API_KEY or USERNAME/PASSWORD basic auth is strongly encouraged if you are exposing this on the open internet. If you set both, the app favors the API_KEY and will look for it in client requests, ignoring USERNAME/PASSWORD.

Some libbeats can use api_key, some can't and only support basic auth. This should allow you to configure to match your environment.

The configuration logic will look first to config.yml for default, then config.dev|prod.yml The serverless.yml configuration sets an env variable called ENVIRONMENT to whatever stage you are deploying so the lambda when deployed will read config.${ENVIRONMENT}.yml. Lastly it will read in the OS environment to allow for any overrides using environment variables.

This should allow you to configure for defaults, dev, test, prod and lambda deployments.

Depending on your environemnt, you may need an ES license (from eshost:9200/_license) placed in license.json. Some libbeats check/configure using it and some don't.

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
  #username: "elastic"
  #password: "changeme"

```

If you are deploying/testing locally, localhost will do. If you deploy this lambda you will get the api gateway address and can use that as shown above to configure (note the /dev/ or /prod/ in the url for the gateway depending on how you've deployed it.)

### browserbeat example
A great example use case is user browser history. To my knowledge the only way to get a complete browser history is with an agent. Network level inspection misses local files, has issues with TLS, proxies, vpns, etc.

https://github.com/MelonSmasher/browserbeat is a [community libbeat package](https://www.elastic.co/guide/en/beats/libbeat/master/community-beats.html) that can send local browser history from almost all browsers.

Configure it like so:

```yaml

output.elasticsearch:
  # Array of hosts to connect to.
  hosts: ["n<apigipperish>g.execute-api.us-west-2.amazonaws.com:443/dev/"]
  #hosts: ["localhost:5000"]

  # Protocol - either `http` (default) or `https`.
  protocol: "https"

```

and start with

```bash
browserbeat -c /path/to/browserbeat.yml
```

and you'll end up with browser history in your firehose endpoint like so

```yaml
details:
  '@timestamp': '2020-08-14T17:56:10.133Z'
  agent:
    ephemeral_id: 0e17e2c0-c5b9-4d6d-806f-fdf224dcc2c4
    hostname: Jeffs-MacBook-Pro.local
    id: f98b0b8e-58be-499d-898f-650d22f07017
    type: browserbeat
    version: 0.0.4-alpha3
  data:
    '@processed': '2020-08-14T10:56:10.133063-07:00'
    '@timestamp': '2020-07-25T22:06:43Z'
    event:
      data:
        client:
          browser: chrome
          hostname:
            hostname: Jeffs-MacBook-Pro.local
            short: Jeffs-MacBook-Pro
          ip_addresses:
          - 192.168.0.103
          platform: darwin
          user: jeff
        entry:
          date: '2020-07-25 22:06:43'
          title: ''
          url: file:///Users/jeff/Documents/defendA/defendA-Fencing-black.svg
          url_data:
            forcequery: false
            fragment: ''
            host: ''
            opaque: ''
            path: /Users/jeff/Documents/defendA/defendA-Fencing-black.svg
            rawfragment: ''
            rawpath: ''
            rawquery: ''
            scheme: file
            user: 'null'
      module: browserbeat-chrome
    host:
      hostname: Jeffs-MacBook-Pro.local
      short: Jeffs-MacBook-Pro
  ecs:
    version: 1.1.0
  host:
    architecture: x86_64
    hostname: Jeffs-MacBook-Pro.local
    id: CC972AC4-AB7A-58AB-BB9C-19036DC8B4DF
    name: Jeffs-MacBook-Pro.local
    os:
      build: 19F101
      family: darwin
      kernel: 19.5.0
      name: Mac OS X
      platform: darwin
      version: 10.15.5
  type: browser.history

```

as an example artifact of opening a local .svg file in chrome.

A caveat that the browserbeat libbeat doesn't seem to support api_key auth, so be careful in your configuration (or send a PR!)


