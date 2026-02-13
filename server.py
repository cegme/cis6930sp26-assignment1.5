"""
MCP Server for Emotion Dataset Analysis

This server provides tools for analyzing the dair-ai/emotion dataset
from Hugging Face. It exposes tools for sampling, counting, searching,
and analyzing emotion distributions.

CIS 6930 - Data Engineering Spring 2026
In-Class Activity: MCP on HiPerGator
"""

import json
import random
from collections import Counter

from datasets import load_dataset
from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("EmotionDataProcessor")

EMOTION_LABELS = {
    0: "sadness",
    1: "joy",
    2: "love",
    3: "anger",
    4: "fear",
    5: "surprise",
}

EMOTION_TO_ID = {v: k for k, v in EMOTION_LABELS.items()}

_dataset = None


def get_dataset():
    """Lazy-load the emotion dataset.

    Returns:
        The emotion dataset from Hugging Face.
    """
    global _dataset
    if _dataset is None:
        logger.info("Loading emotion dataset from Hugging Face...")
        _dataset = load_dataset("dair-ai/emotion", split="train")
        logger.info(f"Loaded {len(_dataset)} samples")
    return _dataset


@mcp.tool()
def get_sample(n: int = 5) -> str:
    """Get n random samples from the emotion dataset.

    Args:
        n: Number of samples to retrieve (default: 5, max: 20)

    Returns:
        JSON string with samples including text and emotion label
    """
    n = min(max(n, 1), 20)  # Clamp to 1-20
    dataset = get_dataset()
    indices = random.sample(range(len(dataset)), n)

    samples = []
    for idx in indices:
        sample = dataset[idx]
        samples.append({
            "text": sample["text"],
            "emotion": EMOTION_LABELS[sample["label"]],
            "index": idx
        })

    return json.dumps(samples, indent=2)


@mcp.tool()
def count_by_emotion(emotion: str) -> str:
    """Count samples for a specific emotion.

    Args:
        emotion: One of 'sadness', 'joy', 'love', 'anger', 'fear', 'surprise'

    Returns:
        JSON string with count and percentage
    """
    emotion = emotion.lower().strip()

    if emotion not in EMOTION_TO_ID:
        return json.dumps({
            "error": f"Invalid emotion. Choose from: {list(EMOTION_TO_ID.keys())}"
        })

    emotion_id = EMOTION_TO_ID[emotion]
    dataset = get_dataset()

    count = sum(1 for sample in dataset if sample["label"] == emotion_id)
    percentage = (count / len(dataset)) * 100

    return json.dumps({
        "emotion": emotion,
        "count": count,
        "total": len(dataset),
        "percentage": round(percentage, 2)
    }, indent=2)


@mcp.tool()
def search_text(query: str, limit: int = 10) -> str:
    """Search for samples containing specific text.

    Args:
        query: Text to search for (case-insensitive)
        limit: Maximum results to return (default: 10)

    Returns:
        JSON string with matching samples
    """
    query = query.lower()
    limit = min(max(limit, 1), 50)
    dataset = get_dataset()

    matches = []
    for idx, sample in enumerate(dataset):
        if query in sample["text"].lower():
            matches.append({
                "text": sample["text"],
                "emotion": EMOTION_LABELS[sample["label"]],
                "index": idx
            })
            if len(matches) >= limit:
                break

    return json.dumps({
        "query": query,
        "found": len(matches),
        "matches": matches
    }, indent=2)


@mcp.tool()
def analyze_emotion_distribution() -> str:
    """Get the distribution of emotions in the dataset.

    Returns:
        JSON string with counts and percentages for each emotion
    """
    dataset = get_dataset()

    counter = Counter(sample["label"] for sample in dataset)
    total = len(dataset)

    distribution = []
    for label_id, count in counter.most_common():
        distribution.append({
            "emotion": EMOTION_LABELS[label_id],
            "count": count,
            "percentage": round((count / total) * 100, 2)
        })

    return json.dumps({
        "total_samples": total,
        "distribution": distribution
    }, indent=2)


if __name__ == "__main__":
    logger.info("Starting EmotionDataProcessor MCP server...")
    mcp.run()
