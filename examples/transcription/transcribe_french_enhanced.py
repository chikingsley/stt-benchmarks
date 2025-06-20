#!/usr/bin/env python3
"""
Enhanced French Audio Transcription with Progress Bars, File Output, and WER Analysis
Uses alive-progress for visual feedback and compares multiple WhisperKit models
"""

import time
import json
import re
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from whisperkit.pipelines import WhisperKit
import jiwer

# Suppress verbose logging from WhisperKit
logging.getLogger("whisperkit.pipelines").setLevel(logging.WARNING)
logging.getLogger("argmaxtools.utils").setLevel(logging.WARNING)


class TranscriptionAnalyzer:
    def __init__(self, audio_path, output_dir="./transcription_results"):
        self.audio_path = Path(audio_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create timestamped subdirectory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)

        self.results = {}
        self.timings = {}

    def transcribe_model(self, model_name, timeout=120):
        """Transcribe with a single model"""

        model_key = model_name.split("/")[-1]
        print(f"🎙️  Transcribing with {model_key}...")

        start_time = time.time()

        try:
            print("  🚀 Initializing model...")

            pipe = WhisperKit(whisper_version=model_name, out_dir="./whisper_output")

            print("  📂 Model loaded, starting transcription...")

            # Manually build and run the command to suppress all output
            cmd = [
                pipe.cli_path,
                "transcribe",
                "--audio-path",
                str(self.audio_path),
                "--model-path",
                pipe.models_dir,
                "--text-decoder-compute-units",
                pipe._text_decoder_compute_units,
                "--audio-encoder-compute-units",
                pipe._audio_encoder_compute_units,
                "--report-path",
                pipe.results_dir,
                "--report",
                "--language",
                "fr",
            ]

            # Set the correct working directory for the Swift process
            swift_project_root = Path(pipe.cli_path).parents[2]

            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=swift_project_root,
            )

            # Manually load the result
            result_path = Path(pipe.results_dir) / f"{self.audio_path.stem}.json"
            with open(result_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            print("  ✅ Transcription complete!")

            duration = time.time() - start_time

            # Check timeout
            if duration > timeout:
                print(f"  ⚠️  Too slow: {duration:.1f}s (>{timeout}s limit)")
                return None, duration

            # Save results
            self._save_model_results(model_key, result, duration)

            print(f"  💾 Saved! Total time: {duration:.1f}s")

            return result, duration

        except (Exception, subprocess.CalledProcessError) as e:
            print(f"  ❌ Failed: {str(e)[:30]}...")
            return None, None

    def _save_model_results(self, model_key, result, duration):
        """Save individual model results to files"""

        model_dir = self.session_dir / model_key
        model_dir.mkdir(exist_ok=True)

        # Save full JSON
        json_path = model_dir / "full_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Save clean text
        text_path = model_dir / "transcription.txt"
        clean_text = self._clean_text(result["text"])
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        # Save SRT if segments available
        if "segments" in result:
            srt_path = model_dir / "subtitles.srt"
            srt_content = self._generate_srt(result["segments"])
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

        # Save timing info
        timing_path = model_dir / "timing.json"
        timing_info = {
            "total_duration_seconds": duration,
            "audio_length_seconds": result.get("timings", {}).get(
                "inputAudioSeconds", 0
            ),
            "language_detected": result.get("language", "unknown"),
            "model_name": model_key,
        }
        with open(timing_path, "w", encoding="utf-8") as f:
            json.dump(timing_info, f, indent=2)

        # Store for comparison
        self.results[model_key] = {
            "result": result,
            "clean_text": clean_text,
            "duration": duration,
        }

    def _clean_text(self, text):
        """Remove timestamp markers and clean up text"""
        # Remove timestamp markers like <|0.00|> and <|startoftranscript|>
        cleaned = re.sub(r"<\|[^|]*\|>", "", text)
        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    def _generate_srt(self, segments):
        """Convert segments to SRT format"""
        srt_lines = []

        for i, seg in enumerate(segments, 1):
            text = self._clean_text(seg["text"])
            if not text:
                continue

            start = self._format_timestamp(seg["start"])
            end = self._format_timestamp(seg["end"])

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")

        return "\n".join(srt_lines)

    def _format_timestamp(self, seconds):
        """Convert seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")

    def calculate_wer_matrix(self):
        """Calculate Word Error Rate between all model pairs"""

        if len(self.results) < 2:
            return None

        print("📊 Calculating WER...")
        wer_matrix = {}
        model_names = list(self.results.keys())

        for i, model1 in enumerate(model_names):
            for j, model2 in enumerate(model_names[i + 1 :], i + 1):
                text1 = self.results[model1]["clean_text"]
                text2 = self.results[model2]["clean_text"]

                # Calculate WER
                wer_score = jiwer.wer(text1, text2)

                pair_key = f"{model1}_vs_{model2}"
                wer_matrix[pair_key] = {
                    "wer": wer_score,
                    "model1": model1,
                    "model2": model2,
                    "reference_text": text1,
                    "hypothesis_text": text2,
                }

                print(f"  🔍 {model1} vs {model2}: WER={wer_score:.3f}")

        # Save WER analysis
        wer_path = self.session_dir / "wer_analysis.json"
        with open(wer_path, "w", encoding="utf-8") as f:
            json.dump(wer_matrix, f, indent=2)

        return wer_matrix

    def generate_analysis_report(self, wer_matrix=None):
        """Generate comprehensive analysis report"""

        report_lines = []
        report_lines.append("# WhisperKit French Transcription Analysis Report")
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append(f"Audio file: {self.audio_path.name}")
        report_lines.append("")

        # Performance Summary
        report_lines.append("## ⚡ Performance Summary")
        report_lines.append("")
        sorted_results = sorted(self.results.items(), key=lambda x: x[1]["duration"])

        for model, data in sorted_results:
            duration = data["duration"]
            language = data["result"].get("language", "unknown")
            text_length = len(data["clean_text"])

            report_lines.append(
                f"- **{model}**: {duration:.1f}s | {language} | {text_length} chars"
            )

        report_lines.append("")

        # Fastest Model
        if sorted_results:
            fastest = sorted_results[0]
            report_lines.append(
                f"🏆 **Fastest**: {fastest[0]} at {fastest[1]['duration']:.1f}s"
            )
            report_lines.append("")

        # WER Analysis
        if wer_matrix:
            report_lines.append("## 📊 Word Error Rate (WER) Analysis")
            report_lines.append("")

            best_wer = min(wer_matrix.values(), key=lambda x: x["wer"])
            worst_wer = max(wer_matrix.values(), key=lambda x: x["wer"])

            for pair_key, wer_data in sorted(
                wer_matrix.items(), key=lambda x: x[1]["wer"]
            ):
                wer_score = wer_data["wer"]
                model1 = wer_data["model1"]
                model2 = wer_data["model2"]

                if wer_score == best_wer["wer"]:
                    emoji = "🎯"
                elif wer_score == worst_wer["wer"]:
                    emoji = "⚠️"
                else:
                    emoji = "📈"

                report_lines.append(
                    f"{emoji} **{model1} vs {model2}**: WER = {wer_score:.3f}"
                )

            report_lines.append("")
            report_lines.append(
                f"🎯 **Most Similar**: {best_wer['model1']} vs {best_wer['model2']} (WER: {best_wer['wer']:.3f})"
            )
            report_lines.append("")

        # File Locations
        report_lines.append("## 📁 Output Files")
        report_lines.append("")
        report_lines.append(f"All results saved to: `{self.session_dir}`")
        report_lines.append("")

        for model in self.results:
            model_dir = self.session_dir / model
            report_lines.append(f"### {model}")
            report_lines.append(f"- Full JSON: `{model_dir}/full_result.json`")
            report_lines.append(f"- Clean text: `{model_dir}/transcription.txt`")
            report_lines.append(f"- Subtitles: `{model_dir}/subtitles.srt`")
            report_lines.append(f"- Timing: `{model_dir}/timing.json`")
            report_lines.append("")

        # Save report
        report_content = "\n".join(report_lines)
        report_path = self.session_dir / "analysis_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_content, report_path


def main():
    audio_path = (
        "./samples/french-i-lesson-01.mp3"
    )

    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return

    # Models to test (same as working transcribe_french.py)
    models_to_test = [
        # "openai/whisper-tiny",
        "openai/whisper-large-v3-v20240930_626MB",
        "openai/whisper-large-v3-v20240930_turbo_632MB",
    ]

    print("🇫🇷 Enhanced WhisperKit French Transcription Analysis")
    print("=" * 60)
    print(f"📁 Audio: {Path(audio_path).name}")
    print(f"🤖 Testing {len(models_to_test)} models")
    print("")

    analyzer = TranscriptionAnalyzer(audio_path)

    # Test each model with appropriate timeouts
    timeouts = {
        "openai/whisper-tiny": 60,
        "openai/whisper-large-v3-v20240930_626MB": 180,
        "openai/whisper-large-v3-v20240930_turbo_632MB": 180,
    }

    for model in models_to_test:
        timeout = timeouts.get(model, 120)
        result, duration = analyzer.transcribe_model(model, timeout=timeout)

        if not result:
            model_name = model.split("/")[-1]
            if "large" in model:
                print(
                    f"⚠️  {model_name} too slow or failed, continuing with analysis..."
                )
                continue
            else:
                print(f"⚠️  {model_name} failed, skipping remaining models")
                break

        time.sleep(1)  # Brief pause between models

    print("")
    print("🔍 Performing analysis...")

    # Calculate WER if we have multiple results
    wer_matrix = None
    if len(analyzer.results) >= 2:
        wer_matrix = analyzer.calculate_wer_matrix()

    # Generate report
    report_content, report_path = analyzer.generate_analysis_report(wer_matrix)

    print("")
    print("✅ Analysis Complete!")
    print(f"📊 Report saved to: {report_path}")
    print("")
    print("=" * 60)
    print(report_content)


if __name__ == "__main__":
    main()
