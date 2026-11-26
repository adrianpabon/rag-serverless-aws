"""Return a pre-signed S3 POST so an authenticated user can upload a document directly to S3.

Flow: API Gateway (REST, Cognito authorizer) -> this Lambda -> pre-signed POST (url + fields).
The client then uploads the file straight to S3, and the ingestion pipeline syncs it.

S3 enforces the policy embedded in the signature: exact key, content type and max size (ADR 0008).
"""

import json
import logging
import os
import re
import uuid

import boto3
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DOCS_BUCKET = os.environ["DOCS_BUCKET"]
UPLOAD_PREFIX = "uploads/"
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
URL_EXPIRES_SECONDS = int(os.environ.get("URL_EXPIRES_SECONDS", "300"))
MAX_NAME_LENGTH = 100

# Formats the Knowledge Base can parse, with the Content-Type S3 will require.
ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html",
    ".csv": "text/csv",
}

s3 = boto3.client("s3", config=Config(signature_version="s3v4"))


def _response(status: int, body: dict) -> dict:
    """Build an API Gateway Lambda proxy response."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _user_sub(event: dict) -> str | None:
    """The Cognito user id, taken from the authorizer claims (never from the request body)."""
    try:
        return event["requestContext"]["authorizer"]["claims"]["sub"]
    except (KeyError, TypeError):
        return None


def _safe_file_name(raw: str) -> str:
    """Keep only the base name and safe characters, so the key can't escape the user's folder."""
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    if not name:
        raise ValueError("Invalid file name.")
    if len(name) > MAX_NAME_LENGTH:
        stem, dot, ext = name.rpartition(".")
        name = f"{stem[: MAX_NAME_LENGTH - len(ext) - 1]}.{ext}" if dot else name[:MAX_NAME_LENGTH]
    return name


def lambda_handler(event: dict, context) -> dict:
    sub = _user_sub(event)
    if not sub:
        return _response(401, {"error": "Unauthorized."})

    try:
        payload = json.loads(event.get("body") or "{}")
        file_name = _safe_file_name(str(payload.get("fileName", "")))
    except (ValueError, json.JSONDecodeError) as error:
        return _response(400, {"error": str(error) or "Invalid request body."})

    extension = os.path.splitext(file_name)[1].lower()
    content_type = ALLOWED_TYPES.get(extension)
    if not content_type:
        allowed = " ".join(sorted(ALLOWED_TYPES))
        return _response(400, {"error": f"File type not allowed. Allowed: {allowed}"})

    key = f"{UPLOAD_PREFIX}{sub}/{uuid.uuid4().hex[:8]}-{file_name}"
    presigned = s3.generate_presigned_post(
        Bucket=DOCS_BUCKET,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, MAX_UPLOAD_BYTES],
        ],
        ExpiresIn=URL_EXPIRES_SECONDS,
    )
    logger.info("Pre-signed POST for %s (%s), expires in %d s.", key, content_type, URL_EXPIRES_SECONDS)

    return _response(
        200,
        {
            "url": presigned["url"],
            "fields": presigned["fields"],
            "key": key,
            "maxBytes": MAX_UPLOAD_BYTES,
            "expiresIn": URL_EXPIRES_SECONDS,
        },
    )
