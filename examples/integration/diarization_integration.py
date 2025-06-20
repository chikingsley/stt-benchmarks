#!/usr/bin/env python3
"""
Speaker Diarization Integration for Kyutai STT
Combines Kyutai streaming transcription with pyannote speaker diarization
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime

class KyutaiDiarizationPipeline:
    def __init__(self, audio_path, output_dir="./diarization_results"):
        self.audio_path = Path(audio_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create timestamped subdirectory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
    def check_diarization_dependencies(self):
        """Check if pyannote.audio is available"""
        try:
            import pyannote.audio
            print("✅ pyannote.audio available")
            return True
        except ImportError:
            print("❌ pyannote.audio not installed")
            print("\nTo install pyannote.audio:")
            print("  poetry add pyannote.audio")
            print("  # or")
            print("  pip install pyannote.audio")
            print("\nYou'll also need a HuggingFace token:")
            print("  https://huggingface.co/settings/tokens")
            return False
    
    def install_diarization_dependencies(self):
        """Install pyannote.audio if needed"""
        print("📦 Installing pyannote.audio...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pyannote.audio"
            ])
            print("✅ pyannote.audio installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install pyannote.audio")
            return False
    
    def transcribe_with_kyutai(self):
        """Get transcription from Kyutai STT"""
        print("🎙️  Running Kyutai transcription...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "moshi.run_inference",
                "--hf-repo", "kyutai/stt-1b-en_fr",
                "--device", "cpu",
                str(self.audio_path)
            ], capture_output=True, text=True, timeout=300)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Extract transcription
                lines = result.stdout.split('\n')
                transcription_lines = []
                
                for line in lines:
                    if not (line.startswith('[') or line.startswith('Info:') or 
                           'loading' in line.lower() or 'processed' in line.lower()):
                        if line.strip():
                            transcription_lines.append(line.strip())
                
                transcription = ' '.join(transcription_lines)
                
                # Save transcription
                trans_path = self.session_dir / "kyutai_transcription.txt"
                with open(trans_path, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                print(f"✅ Kyutai transcription complete ({duration:.1f}s)")
                return transcription, duration
            else:
                print(f"❌ Kyutai transcription failed: {result.stderr}")
                return None, duration
                
        except subprocess.TimeoutExpired:
            print("❌ Kyutai transcription timed out")
            return None, 300
        except Exception as e:
            print(f"❌ Kyutai transcription error: {e}")
            return None, time.time() - start_time
    
    def run_speaker_diarization(self, hf_token=None):
        """Run speaker diarization with pyannote"""
        print("👥 Running speaker diarization...")
        
        try:
            from pyannote.audio import Pipeline
            import torch
            
            # Load pipeline
            if hf_token:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
            else:
                print("⚠️  No HuggingFace token provided - using public model")
                # Try without token (may not work for latest models)
                pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
            
            # Use GPU if available
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            if device.type == "cuda":
                print("🚀 Using GPU for diarization")
                pipeline.to(device)
            else:
                print("💻 Using CPU for diarization")
            
            start_time = time.time()
            
            # Run diarization
            diarization = pipeline(str(self.audio_path))
            
            duration = time.time() - start_time
            
            # Convert to list format for JSON serialization
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                    "duration": turn.end - turn.start
                })
            
            # Save diarization results
            diar_path = self.session_dir / "speaker_diarization.json"
            with open(diar_path, 'w') as f:
                json.dump({
                    "segments": segments,
                    "duration": duration,
                    "num_speakers": len(set(seg["speaker"] for seg in segments))
                }, f, indent=2)
            
            print(f"✅ Speaker diarization complete ({duration:.1f}s)")
            print(f"👥 Detected {len(set(seg['speaker'] for seg in segments))} speakers")
            
            return segments, duration
            
        except ImportError:
            print("❌ pyannote.audio not available")
            return None, 0
        except Exception as e:
            print(f"❌ Diarization error: {e}")
            return None, 0
    
    def combine_transcription_and_diarization(self, transcription, diarization_segments):
        """Combine Kyutai transcription with speaker labels"""
        print("🔄 Combining transcription with speaker labels...")
        
        # For now, this is a simple approach
        # In production, you'd need timestamp alignment between Kyutai and diarization
        
        combined_result = {
            "transcription": transcription,
            "speakers": diarization_segments,
            "combined_format": "Note: Advanced timestamp alignment needed for precise speaker-text mapping"
        }
        
        # Create a simple speaker timeline
        speaker_timeline = []
        for seg in diarization_segments:
            speaker_timeline.append(f"{seg['start']:.1f}s - {seg['end']:.1f}s: {seg['speaker']}")
        
        combined_result["speaker_timeline"] = speaker_timeline
        
        # Save combined results
        combined_path = self.session_dir / "combined_results.json"
        with open(combined_path, 'w') as f:
            json.dump(combined_result, f, indent=2, ensure_ascii=False)
        
        return combined_result
    
    def generate_summary_report(self, transcription, diarization_segments, kyutai_time, diar_time):
        """Generate a summary report"""
        
        report_lines = []
        report_lines.append("# Kyutai + Diarization Results")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Audio: {self.audio_path.name}")
        report_lines.append("")
        
        # Performance summary
        report_lines.append("## Performance")
        report_lines.append(f"- Kyutai transcription: {kyutai_time:.1f}s")
        report_lines.append(f"- Speaker diarization: {diar_time:.1f}s")
        report_lines.append(f"- Total processing: {kyutai_time + diar_time:.1f}s")
        report_lines.append("")
        
        # Speaker analysis
        if diarization_segments:
            speakers = set(seg["speaker"] for seg in diarization_segments)
            report_lines.append(f"## Speaker Analysis")
            report_lines.append(f"- Number of speakers detected: {len(speakers)}")
            report_lines.append("")
            
            for speaker in sorted(speakers):
                speaker_segs = [seg for seg in diarization_segments if seg["speaker"] == speaker]
                total_time = sum(seg["duration"] for seg in speaker_segs)
                report_lines.append(f"### {speaker}")
                report_lines.append(f"- Speaking time: {total_time:.1f}s")
                report_lines.append(f"- Number of segments: {len(speaker_segs)}")
                report_lines.append("")
        
        # Transcription
        report_lines.append("## Transcription")
        report_lines.append("```")
        report_lines.append(transcription or "No transcription available")
        report_lines.append("```")
        report_lines.append("")
        
        # Integration notes
        report_lines.append("## Integration Notes")
        report_lines.append("- Kyutai provides excellent real-time transcription")
        report_lines.append("- Pyannote provides accurate speaker identification")
        report_lines.append("- For precise speaker-text alignment, timestamp synchronization is needed")
        report_lines.append("- Consider hybrid approach: Kyutai for live captions + post-processing diarization")
        
        # Save report
        report_content = "\\n".join(report_lines)
        report_path = self.session_dir / "summary_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_content, report_path
    
    def run_complete_pipeline(self, hf_token=None):
        """Run the complete pipeline: transcription + diarization"""
        print("🚀 Kyutai + Diarization Pipeline")
        print("=" * 50)
        print(f"📁 Audio: {self.audio_path.name}")
        print(f"📂 Output: {self.session_dir}")
        print("")
        
        # Check dependencies
        if not self.check_diarization_dependencies():
            install_choice = input("Install pyannote.audio? (y/n): ")
            if install_choice.lower() == 'y':
                if not self.install_diarization_dependencies():
                    print("❌ Cannot proceed without pyannote.audio")
                    return
            else:
                print("❌ Cannot proceed without pyannote.audio")
                return
        
        # Step 1: Kyutai transcription
        transcription, kyutai_time = self.transcribe_with_kyutai()
        
        # Step 2: Speaker diarization
        diarization_segments, diar_time = self.run_speaker_diarization(hf_token)
        
        # Step 3: Combine results
        if transcription and diarization_segments:
            combined = self.combine_transcription_and_diarization(transcription, diarization_segments)
            print("✅ Successfully combined transcription and diarization")
        
        # Step 4: Generate report
        report_content, report_path = self.generate_summary_report(
            transcription, diarization_segments, kyutai_time, diar_time
        )
        
        print("")
        print("✅ Pipeline Complete!")
        print(f"📄 Report: {report_path}")
        print(f"📁 All files: {self.session_dir}")
        
        # Show quick summary
        if diarization_segments:
            speakers = set(seg["speaker"] for seg in diarization_segments)
            print(f"👥 Detected {len(speakers)} speakers")
            
        if transcription:
            print(f"📝 Transcription: {len(transcription)} characters")

def main():
    audio_path = "./samples/french-i-lesson-01-30s.mp3"
    
    if not Path(audio_path).exists():
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    # Initialize pipeline
    pipeline = KyutaiDiarizationPipeline(audio_path)
    
    # Get HuggingFace token
    hf_token = input("HuggingFace token (optional, press Enter to skip): ").strip()
    if not hf_token:
        hf_token = None
    
    # Run pipeline
    pipeline.run_complete_pipeline(hf_token)

if __name__ == "__main__":
    main()