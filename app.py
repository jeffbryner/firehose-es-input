import base64
import logging.config
import boto3
from botocore.errorfactory import ClientError
from datetime import datetime
import io
import json
import yaml
import os
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
    make_response,
    send_from_directory,
    send_file,
    jsonify,
    Response,
)
from utils.config import get_config
from functools import wraps
import random

logger = logging.getLogger()
with open("logging_config.yml", "r") as fd:
    logging_config = yaml.safe_load(fd)
    logging.config.dictConfig(logging_config)

logger.setLevel(logging.INFO)

app = Flask(__name__)
config = get_config()

FIREHOSE_DELIVERY_STREAM = os.environ.get(
    "FIREHOSE_DELIVERY_STREAM", "data_lake_s3_stream"
)
FIREHOSE_BATCH_SIZE = os.environ.get("FIREHOSE_BATCH_SIZE", 400)
f_hose = boto3.client("firehose")


def is_authorized(headers):
    """ check headers for Authorization ApiKey <base64>
        if config.API_KEY is set to something
        used by the check_apikey decorator
    """

    authorized = False
    try:
        if "API_KEY" in config and config.API_KEY:
            if "Authorization" in headers:
                # should be ApiKey aWQ6YXBpX2tleV9nb2VzX2hlcmU=
                # where the value is id:key base64 encoded
                apikey_base64 = headers["Authorization"].split(" ")[1]
                apikey = base64.b64decode(apikey_base64).decode("utf-8").split(":")[1]
                if apikey == config.API_KEY:
                    # logger.debug(f"valid api key {apikey}")
                    authorized = True
                else:
                    logger.error(f"invalid api key: {apikey}")
            else:
                logger.error(f"no Authorization header found in incoming request")
        else:
            logger.debug(f"no api key found in config, allowing all requests")
            authorized = True
    except Exception as e:
        logger.error(f"Exception {e} while trying to validate authorization header")
    finally:
        return authorized


def check_apikey(view_function):
    @wraps(view_function)
    # the new, post-decoration function
    def decorated_function(*args, **kwargs):
        if is_authorized(request.headers):
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


def generate_ID():
    return "%020x" % random.randrange(16 ** 20)


def send_to_firehose(records):
    # records should be a list of dicts
    if type(records) is list:
        # batch up the list below the limits of firehose
        for batch in chunks(records, FIREHOSE_BATCH_SIZE):
            response = f_hose.put_record_batch(
                DeliveryStreamName=FIREHOSE_DELIVERY_STREAM,
                Records=[
                    {"Data": bytes(str(json.dumps(record) + "\n").encode("UTF-8"))}
                    for record in batch
                ],
            )
            logger.debug("firehose response is: {}".format(response))


@app.route("/")
@check_apikey
def default_return():
    status = json.loads(
        r"""{
            "name": "6a11ece568ff",
            "cluster_name": "docker-cluster",
            "cluster_uuid": "YbgvRgp8Tjivhxo5VU_4sg",
            "version": {
                "number": "7.8.1",
                "build_flavor": "default",
                "build_type": "docker",
                "build_hash": "b5ca9c58fb664ca8bf9e4057fc229b3396bf3a89",
                "build_date": "2020-07-21T16:40:44.668009Z",
                "build_snapshot": false,
                "lucene_version": "8.5.1",
                "minimum_wire_compatibility_version": "6.8.0",
                "minimum_index_compatibility_version": "6.0.0-beta1"
            },
            "tagline": "You Know, for Search"
        }"""
    )
    return jsonify(status)


@app.route("/_license")
@check_apikey
def license_endpoint():
    # place your ES license (from eshost:9200/_license) in license.json
    license = json.loads(open("license.json").read())
    return jsonify(license)


@app.route("/_xpack")
@check_apikey
def xpack_endpoint():
    # let the caller know we don't support anything
    xpack = json.loads(
        r"""
    {"build":{"hash":"b5ca9c58fb664ca8bf9e4057fc229b3396bf3a89",
    "date":"2020-07-21T16:40:44.668009Z"},
    "license":{"uid":"39710247-c89c-46c0-9e0a-916e788853ac",
    "type":"basic","mode":"basic","status":"active"},
    "features":
    {"analytics":{"available":false,"enabled":false},
    "ccr":{"available":false,"enabled":false},
    "enrich":{"available":false,"enabled":false},
    "eql":{"available":false,"enabled":false},
    "flattened":{"available":false,"enabled":false},
    "frozen_indices":{"available":false,"enabled":false},
    "graph":{"available":false,"enabled":false},
    "ilm":{"available":false,"enabled":false},
    "logstash":{"available":false,"enabled":false},
    "ml":{"available":false,"enabled":false,
    "native_code_info":{"version":"7.8.1","build_hash":"d0d3f60f03220d"}},
    "monitoring":{"available":false,"enabled":false},
    "rollup":{"available":false,"enabled":false},
    "security":{"available":false,"enabled":false},
    "slm":{"available":false,"enabled":false},
    "spatial":{"available":false,"enabled":false},
    "sql":{"available":false,"enabled":false},
    "transform":{"available":false,"enabled":false},
    "vectors":{"available":false,"enabled":false},
    "voting_only":{"available":false,"enabled":false},
    "watcher":{"available":false,"enabled":false}},
    "tagline":"You know, for X"}
    """
    )
    return jsonify(xpack)


@app.route("/_cat/<path:request_path>")
@app.route("/_ilm/policy/<path:policy_path>")
@check_apikey
def fake_endpoint(request_path):
    # nothing here
    return ""


@app.route("/_alias/<path:alias_path>")
@check_apikey
def fake_alias(alias_path):
    alias_output = {}
    alias_output[
        f"{alias_path}-{datetime.utcnow().year}.{datetime.utcnow().month}.{datetime.utcnow().day}-000001"
    ] = {"aliases": {alias_path: {"is_write_index": True}}}
    return jsonify(alias_output)


@app.route("/_template/<path:request_path>", methods=["GET", "PUT"])
@check_apikey
def template_endpoint(request_path):
    logging.debug(request_path)
    return ""


@app.route("/status")
@app.route("/status/")
def status_page():
    return "ok!"


@app.route("/_bulk", methods=["POST", "PUT"])
@check_apikey
def bulk_index():
    ack_shell = json.loads(
        r"""
    {
        "create": {
            "_index": "",
            "_type": "_doc",
            "_id": "",
            "_version": 1,
            "result": "created",
            "_shards": {
                "total": 1,
                "successful": 1,
                "failed": 0
            },
            "_seq_no": 1,
            "_primary_term": 1,
            "status": 201
        }
    }
    """
    )

    items = request.data.splitlines()
    out_items = []
    return_items = []
    index = "default-index"
    for i in items:
        item = json.loads(i)
        if "create" in item:
            # instruction to create/save a document
            # get the index info to return as success
            index = item["create"]["_index"]
        elif "@timestamp" in item:
            # the actual document
            out_items.append(item)
            ack = ack_shell
            ack["create"]["_index"] = index
            ack["create"]["_id"] = generate_ID()
            ack["create"]["_seq_no"] = random.randint(1000, 90000)
            return_items.append(ack)

    send_to_firehose(out_items)
    return jsonify({"took": 9200, "errors": False, "items": return_items})


if __name__ == "__main__":
    app.run(debug=True)
