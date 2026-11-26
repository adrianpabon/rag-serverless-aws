"""Trigger a Bedrock Knowledge Base sync when documents change in S3.

Flow: S3 (uploads/) -> EventBridge -> SQS -> this Lambda -> StartIngestionJob.

StartIngestionJob re-scans the whole data source, so one call covers every
message in the batch. Bedrock runs one ingestion job at a time per data source:
on ConflictException the batch is reported as failed and SQS redelivers it
after the visibility timeout (see docs/adr/0006).
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
DATA_SOURCE_ID = os.environ["DATA_SOURCE_ID"]

bedrock_agent = boto3.client("bedrock-agent")


def _object_key(record: dict) -> str | None:
    """Return the S3 object key from an SQS record that wraps an EventBridge S3 event."""
    try:
        body = json.loads(record["body"])
        return body["detail"]["object"]["key"]
    except (KeyError, TypeError, json.JSONDecodeError):
        logger.warning("Skipping malformed message %s", record.get("messageId"))
        return None


def _is_document(key: str | None) -> bool:
    """Ignore folder placeholders such as 'uploads/' created by the S3 console."""
    return bool(key) and not key.endswith("/")


def lambda_handler(event: dict, context) -> dict:
    records = event.get("Records", [])
    documents = [r for r in records if _is_document(_object_key(r))]

    if not documents:
        logger.info("No document changes in %d message(s). Nothing to sync.", len(records))
        return {"batchItemFailures": []}

    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID,
            description=f"Triggered by {len(documents)} S3 change(s)",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConflictException":
            logger.warning(
                "An ingestion job is already running. Returning %d message(s) to the queue for retry.",
                len(documents),
            )
            return {"batchItemFailures": [{"itemIdentifier": r["messageId"]} for r in documents]}
        raise  # Any other error: fail the whole batch, SQS retries, then DLQ.

    job = response["ingestionJob"]
    logger.info(
        "Started ingestion job %s (status %s) for %d change(s).",
        job["ingestionJobId"],
        job["status"],
        len(documents),
    )
    return {"batchItemFailures": []}
