#!/usr/bin/env python3
"""
Analyzes Pimsleur lesson transcripts with chunked batch processing and real-time progress.
V2: Robust, resumable extraction with state-of-the-art CLI visualization.
"""

import os
import json
import pathlib
import sys
import time
import re
from typing import List, Optional, TypedDict
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import spacy
from alive_progress import alive_bar  # type: ignore

import csv

load_dotenv()

# ----- Configuration -------------------------------------------------------
BATCH_SIZE = 8
MODEL_CASCADE = [
    "mistral-medium-latest",
    "mistral-large-latest",
    "magistral-medium-latest",
    "magistral-small-latest",
    "mistral-small-latest",
]
RETRY_DELAY = 5  # seconds

# ----- NLP and API Setup ---------------------------------------------------
try:
    NLP = spacy.load("fr_core_news_sm")
except OSError:
    print("Spacy French model 'fr_core_news_sm' not found.")
    print("Please run: poetry run python -m spacy download fr_core_news_sm")
    sys.exit(1)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("MISTRAL_API_KEY not found.")
    print(
        "Please create a .env file in the 'pimsleur-data' directory and add your key:"
    )
    print('MISTRAL_API_KEY="your_mistral_api_key"')
    sys.exit(1)

MISTRAL_CLIENT = MistralClient(
    api_key=MISTRAL_API_KEY, timeout=60
)  # Shorter timeout per batch


# ----- Data Structures -----------------------------------------------------
class Utterance(TypedDict):
    """Represents a single utterance with its metadata."""

    speaker: str
    text: str
    position: int


@dataclass
class UtteranceBatch:
    """Represents a batch of utterances to process."""

    batch_id: int
    utterances: List[Utterance]
    start_position: int
    end_position: int


@dataclass
class UtteranceRecord:
    """Represents a processed utterance record."""

    lesson_number: int
    position_in_lesson: int
    speaker: str
    text: str
    utterance_type: Optional[str]
    narrator_cue: Optional[str]
    core_lemmas: Optional[str]


@dataclass
class ProcessingStatus:
    """Tracks overall processing status."""

    total_batches: int
    completed_batches: int = 0
    failed_batches: int = 0
    total_utterances: int = 0
    processed_utterances: int = 0
    failed_utterances: int = 0
    start_time: float = 0.0
    current_batch: Optional[int] = None
    current_model: str = ""
    last_utterance: str = ""


# ----- Transcript Parsing --------------------------------------------------
def parse_transcript_to_batches(
    transcript: str, batch_size: int = BATCH_SIZE
) -> List[UtteranceBatch]:
    """Parse transcript into batches of utterances."""
    utterances: List[Utterance] = []
    current_speaker = None
    current_text: List[str] = []

    lines = transcript.strip().split("\n")
    position = 0

    for line in lines:
        line = line.strip()

        # Check if this is a speaker tag
        speaker_match = re.match(r"^\[(.*?)\]$", line)

        if speaker_match:
            # Save previous utterance if it's from Male/Female Speaker
            if (
                current_speaker in ["Male Speaker", "Female Speaker"]
                and current_text
                and current_speaker is not None
            ):
                utterance_text = " ".join(current_text).strip()
                if utterance_text and any(char.isalpha() for char in utterance_text):
                    position += 1
                    utterances.append(
                        Utterance(
                            speaker=current_speaker,
                            text=utterance_text,
                            position=position,
                        )
                    )

            # Update current speaker
            current_speaker = speaker_match.group(1)
            current_text = []
        else:
            # Add to current text if we have a speaker
            if current_speaker and line:
                current_text.append(line)

    # Don't forget the last utterance
    if (
        current_speaker in ["Male Speaker", "Female Speaker"]
        and current_text
        and current_speaker is not None
    ):
        utterance_text = " ".join(current_text).strip()
        if utterance_text and any(char.isalpha() for char in utterance_text):
            position += 1
            utterances.append(
                Utterance(
                    speaker=current_speaker,
                    text=utterance_text,
                    position=position,
                )
            )

    # Create batches
    batches: List[UtteranceBatch] = []
    for i in range(0, len(utterances), batch_size):
        batch_utterances = utterances[i : i + batch_size]
        if batch_utterances:
            batch = UtteranceBatch(
                batch_id=len(batches) + 1,
                utterances=batch_utterances,
                start_position=batch_utterances[0]["position"],
                end_position=batch_utterances[-1]["position"],
            )
            batches.append(batch)

    return batches


# ----- Batch Processing ----------------------------------------------------
def process_batch_with_llm(
    batch: UtteranceBatch, lesson_number: int, model_name: str
) -> List[UtteranceRecord]:
    """Process a single batch of utterances with the LLM."""

    # Create a mini-transcript for this batch
    batch_transcript = []
    for utt in batch.utterances:
        batch_transcript.append(f"[{utt['speaker']}]")
        batch_transcript.append(utt["text"])
        batch_transcript.append("")

    batch_text = "\n".join(batch_transcript)

    system_prompt = """
You are analyzing a segment of a Pimsleur French lesson. For each French utterance by Male Speaker or Female Speaker, provide:

1. `utterance_text`: The exact French phrase
2. `speaker`: 'Male Speaker' or 'Female Speaker'
3. `utterance_type`: One of:
   - `DirectRepetition`: Repeating after narrator
   - `PromptedRecall`: Responding to narrator prompt
   - `ConversationalExchange`: Part of dialogue
   - `SimpleResponse`: Short phrase like "Oui" or "Non"
4. `narrator_cue`: The narrator instruction that prompted it (if any)
5. `core_lemmas`: List of lemma forms of main words

Return a JSON object with key "analyzed_utterances" containing a list of utterance analyses.
"""

    user_prompt = f"Analyze these utterances from positions {batch.start_position} to {batch.end_position}:\n\n{batch_text}"

    try:
        response = MISTRAL_CLIENT.chat(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ],
            temperature=0.0,
        )

        data = json.loads(response.choices[0].message.content)
        analyzed_utterances = data.get("analyzed_utterances")

        # Validate the structure of the response
        if not isinstance(analyzed_utterances, list):
            print(
                f"\n⚠️  'analyzed_utterances' is not a list in batch {batch.batch_id}. Content: {str(analyzed_utterances)[:100]}"
            )
            return []

        # Convert to UtteranceRecord objects
        utterances = []
        for idx, (item, original) in enumerate(
            zip(analyzed_utterances, batch.utterances)
        ):
            if not isinstance(item, dict):
                print(
                    f"\n⚠️  Item {idx} in batch {batch.batch_id} is not a dictionary. Skipping."
                )
                continue

            utterances.append(
                UtteranceRecord(
                    lesson_number=lesson_number,
                    position_in_lesson=original["position"],
                    speaker=item.get("speaker", original["speaker"]),
                    text=item.get("utterance_text", original["text"]),
                    utterance_type=item.get("utterance_type"),
                    narrator_cue=item.get("narrator_cue", ""),
                    core_lemmas=" ".join(item.get("core_lemmas", [])),
                )
            )

        return utterances

    except Exception as e:
        print(f"\n⚠️  Error processing batch {batch.batch_id}: {str(e)[:100]}")
        return []


# ----- CSV Writer ----------------------------------------------------------
def write_to_csv(utterances: List[UtteranceRecord], output_path: pathlib.Path):
    """Write utterances to CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "lesson_number",
            "position_in_lesson",
            "speaker",
            "text",
            "utterance_type",
            "narrator_cue",
            "core_lemmas",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for utterance in utterances:
            writer.writerow(asdict(utterance))


# ----- Main Processing Function --------------------------------------------
def process_lesson_chunked(file_path: pathlib.Path, output_dir: pathlib.Path) -> int:
    """Process a lesson file using chunked batch processing with alive_progress."""

    # Extract lesson number
    lesson_number = int(file_path.stem.split("_")[4])
    lesson_name = file_path.stem

    # Read transcript
    transcript = file_path.read_text("utf-8")

    # Parse into batches
    batches = parse_transcript_to_batches(transcript, BATCH_SIZE)

    if not batches:
        print(f"⚠️  No utterances found in {file_path.name}")
        return 0

    # Initialize status
    status = ProcessingStatus(
        total_batches=len(batches),
        total_utterances=sum(len(b.utterances) for b in batches),
        start_time=time.time(),
        current_model=MODEL_CASCADE[0],
    )

    # Process each batch with alive progress bar
    all_utterances = []

    print(f"\n📖 Processing {lesson_name}")
    print(
        f"📊 Total utterances: {status.total_utterances} in {status.total_batches} batches"
    )

    # Use alive_bar with optimized settings for smooth performance
    with alive_bar(
        status.total_batches,
        title="🚀 Extracting utterances",
        spinner="waves",
        dual_line=True,
        length=40,
        force_tty=True,
        refresh_secs=0.05,  # Faster refresh for smoother animation
    ) as bar:
        for batch in batches:
            status.current_batch = batch.batch_id

            # Try processing with model cascade
            success = False
            batch_utterances = []

            for attempt, model_to_try in enumerate(MODEL_CASCADE):
                status.current_model = model_to_try
                # Only update text once per batch, not per model attempt
                if attempt == 0:
                    bar.text = f"📦 Batch {batch.batch_id}/{status.total_batches} | ✅ {status.processed_utterances} | ❌ {status.failed_utterances}"

                # Process batch
                batch_utterances = process_batch_with_llm(
                    batch, lesson_number, model_to_try
                )

                if batch_utterances:
                    success = True
                    break  # Success, exit the model cascade loop
                else:
                    if attempt < len(MODEL_CASCADE) - 1:
                        next_model = MODEL_CASCADE[attempt + 1]
                        print(
                            f"\n🔁 Batch {batch.batch_id} failed with {model_to_try}. Retrying with {next_model}..."
                        )
                        time.sleep(RETRY_DELAY)
                    else:
                        print(
                            f"\n❌ All models in cascade failed for batch {batch.batch_id}"
                        )

            # Handle results
            if success and batch_utterances:
                # Add to our collection
                all_utterances.extend(batch_utterances)

                status.completed_batches += 1
                status.processed_utterances += len(batch_utterances)
                status.last_utterance = (
                    batch_utterances[-1].text if batch_utterances else ""
                )

                # Simplified success text (less frequent updates)
                bar.text = f"✅ {status.processed_utterances}/{status.total_utterances} utterances"
            else:
                status.failed_batches += 1
                status.failed_utterances += len(batch.utterances)
                bar.text = f"❌ Failed: {status.failed_utterances} | ✅ Success: {status.processed_utterances}"

            # Update progress bar
            bar()

    # Write to CSV
    output_path = output_dir / f"lesson_{lesson_number:02d}_utterances.csv"
    write_to_csv(all_utterances, output_path)

    # Final summary
    elapsed = time.time() - status.start_time

    print(f"\n{'=' * 60}")
    print(f"✅ Completed: {lesson_name}")
    print(
        f"📊 Results: {status.processed_utterances}/{status.total_utterances} utterances"
    )
    print(f"⏱️  Time: {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print(
        f"🎯 Success rate: {(status.processed_utterances / status.total_utterances * 100):.1f}%"
    )
    if status.failed_batches > 0:
        print(f"⚠️  Failed batches: {status.failed_batches}/{status.total_batches}")
    print(f"💾 Saved to: {output_path}")

    return status.processed_utterances


# ----- Main Function -------------------------------------------------------
def main():
    """Main function with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pimsleur Utterance Extraction - CSV Output Version"
    )
    parser.add_argument(
        "--lessons",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4, 5],
        help="Lesson numbers to process (default: 1 2 3 4 5)",
    )
    # Need to declare global before using it
    global BATCH_SIZE

    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Utterances per batch (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="analysis",
        help="Output directory for CSV files (default: analysis)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="This argument is ignored. The script uses a hardcoded model cascade.",
    )

    args = parser.parse_args()

    # Update batch size if specified
    if args.batch_size:
        BATCH_SIZE = args.batch_size

    # Setup
    project_root = pathlib.Path(__file__).parent.parent
    source_dir = project_root / "01_raw_data" / "transcripts"
    output_dir = project_root / "02_scripts" / args.output_dir

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    if args.model:
        print(
            "⚠️  Warning: The --model argument is ignored. Using the built-in MODEL_CASCADE."
        )

    print("🚀 Pimsleur Utterance Extraction - CSV Output Version")
    print("=" * 60)
    print(f"📖 Using model cascade: {', '.join(MODEL_CASCADE)}")
    print(f"📦 Batch size: {BATCH_SIZE} utterances")
    print(f"📚 Lessons: {args.lessons}")
    print(f"💾 Output directory: {output_dir}")
    print("=" * 60)

    # Process lessons
    total_processed = 0

    for lesson_num in args.lessons:
        file_path = source_dir / f"French_I_-_Lesson_{lesson_num:02d}_human_eval.txt"

        if not file_path.exists():
            print(f"\n❌ File not found: {file_path}")
            continue

        count = process_lesson_chunked(file_path, output_dir)
        total_processed += count

    # Final summary
    print(f"\n{'=' * 60}")
    print("🎉 All lessons complete!")
    print(f"📊 Total utterances processed: {total_processed}")
    print(f"💾 All CSV files saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
