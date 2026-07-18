"""Utility helpers: loading data, logging setup, validation, prompts."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Set

import pandas as pd

from .config import LOG_DIR, SUCCESS_LOG_PATH, ERROR_LOG_PATH

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    # Success file handler
    success_handler = logging.FileHandler(SUCCESS_LOG_PATH, mode="a")
    success_handler.setLevel(logging.INFO)
    success_handler.setFormatter(formatter)
    success_handler.addFilter(lambda record: record.levelno == logging.INFO)
    root.addHandler(success_handler)

    # Error file handler
    error_handler = logging.FileHandler(ERROR_LOG_PATH, mode="a")
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def load_recipients(path: Path) -> Tuple[List[Dict[str, str]], Set[str], Set[str]]:
    """Load recipients from CSV or JSON.

    Returns list of dict rows, set of invalid emails, and set of duplicated emails skipped.
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".json", ".jsonl"}:
        df = pd.read_json(path)
    else:
        raise ValueError("Input file must be CSV or JSON")

    if "email" not in df.columns:
        raise ValueError("Input data must include an 'email' column")

    invalid_emails: Set[str] = set()
    duplicates: Set[str] = set()
    seen: Set[str] = set()
    rows: List[Dict[str, str]] = []

    for _, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        if not validate_email(email):
            invalid_emails.add(email)
            continue
        if email in seen:
            duplicates.add(email)
            continue
        seen.add(email)
        rows.append({k: ("" if pd.isna(v) else str(v)) for k, v in row.items()})

    return rows, invalid_emails, duplicates


def prompt_yes_no(message: str) -> bool:
    while True:
        choice = input(f"{message} [y/n]: ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def load_sent_history(log_path: Path = SUCCESS_LOG_PATH) -> Set[str]:
    """Return set of emails that have already succeeded (used for resume)."""
    if not log_path.exists():
        return set()
    sent: Set[str] = set()
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            if "| INFO |" in line:
                msg = line.split("|")[-1].strip()
                if msg.startswith("SENT"):
                    tokens = msg.split()
                    if len(tokens) >= 2:
                        sent.add(tokens[1])
    return sent
