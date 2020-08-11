import base64
import logging
import boto3
from botocore.errorfactory import ClientError
import io
import json
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

app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@app.route("/status")
@app.route("/status/")
def status_page():
    return "ok!"


if __name__ == "__main__":
    app.run()
