"""Answer a question with RAG: Retrieve chunks from the Knowledge Base, then Converse with Claude.

Flow: API Gateway (REST, Cognito authorizer) -> this Lambda -> Retrieve -> Converse.

Two layers against hallucinations (see docs/adr):
1. If no chunk scores >= MIN_SCORE, return "I don't know" without calling the LLM (free, deterministic).
2. The system prompt tells the model to answer only from the provided context.
"""

import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
MODEL_ID = os.environ["MODEL_ID"]
MIN_SCORE = float(os.environ.get("MIN_SCORE", "0.6"))
NUMBER_OF_RESULTS = int(os.environ.get("NUMBER_OF_RESULTS", "5"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "512"))
MAX_QUESTION_LENGTH = 1000
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

NO_ANSWER = "I don't have information about that in the documents."

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about internal company documents. "
    "Answer ONLY with information from the context provided in <source> tags. "
    "If the context doesn't contain the answer, say that you don't have that information. "
    "Never use outside knowledge and never invent facts. "
    "Be concise, and cite the sources you used as [1], [2], etc."
)

agent_runtime = boto3.client("bedrock-agent-runtime")
bedrock_runtime = boto3.client("bedrock-runtime")


def _response(status: int, body: dict) -> dict:
    """Build an API Gateway Lambda proxy response."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": ALLOWED_ORIGIN},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_question(event: dict) -> str:
    """Accept an API Gateway proxy event (body is a JSON string) or a direct test event."""
    payload = event
    if "body" in event:
        payload = json.loads(event["body"] or "{}")
    question = str(payload.get("question", "")).strip()
    if not question:
        raise ValueError("The 'question' field is required.")
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f"The question must have at most {MAX_QUESTION_LENGTH} characters.")
    return question


def _retrieve(question: str) -> list[dict]:
    """Return the chunks whose score passes the threshold, best first."""
    response = agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": NUMBER_OF_RESULTS}},
    )
    chunks = [
        {
            "text": result["content"]["text"],
            "file": result["location"]["s3Location"]["uri"].rsplit("/", 1)[-1],
            "score": round(result.get("score", 0.0), 3),
        }
        for result in response["retrievalResults"]
    ]
    return [c for c in chunks if c["score"] >= MIN_SCORE]


def _generate(question: str, chunks: list[dict]) -> tuple[str, dict]:
    """Ask the model to answer using only the retrieved chunks."""
    context = "\n\n".join(
        f'<source id="{i}" file="{c["file"]}">\n{c["text"]}\n</source>' for i, c in enumerate(chunks, start=1)
    )
    response = bedrock_runtime.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": f"{context}\n\nQuestion: {question}"}]}],
        inferenceConfig={"maxTokens": MAX_TOKENS},
    )
    answer = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})
    return answer, {"inputTokens": usage.get("inputTokens"), "outputTokens": usage.get("outputTokens")}


def lambda_handler(event: dict, context) -> dict:
    try:
        question = _parse_question(event)
    except (ValueError, json.JSONDecodeError) as error:
        return _response(400, {"error": str(error)})

    try:
        chunks = _retrieve(question)
        logger.info("Question of %d chars: %d chunk(s) passed MIN_SCORE=%s.", len(question), len(chunks), MIN_SCORE)

        if not chunks:
            return _response(200, {"answer": NO_ANSWER, "sources": [], "usage": None})

        answer, usage = _generate(question, chunks)
        sources = [{"id": i, "file": c["file"], "score": c["score"]} for i, c in enumerate(chunks, start=1)]
        logger.info("Answered with %s.", usage)
        return _response(200, {"answer": answer, "sources": sources, "usage": usage})

    except ClientError as error:
        code = error.response["Error"]["Code"]
        logger.exception("Bedrock error: %s", code)
        if code == "ThrottlingException":
            return _response(429, {"error": "Too many requests. Please try again in a moment."})
        return _response(500, {"error": "Internal error."})
