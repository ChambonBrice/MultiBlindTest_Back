import os
import uuid
import subprocess
from pathlib import Path


class AudioService:
    BASE_DIR = Path(__file__).resolve().parent.parent
    STORAGE_DIR = BASE_DIR / "storage"
    TRACKS_DIR = STORAGE_DIR / "tracks"
    CLIPS_DIR = STORAGE_DIR / "clips"

    @classmethod
    def ensure_directories(cls):
        cls.TRACKS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def download_audio_from_youtube(cls, youtube_url: str) -> tuple[str, int]:
        cls.ensure_directories()

        file_id = str(uuid.uuid4())
        output_template = cls.TRACKS_DIR / f"{file_id}.%(ext)s"
        final_mp3 = cls.TRACKS_DIR / f"{file_id}.mp3"

        subprocess.run([
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--output", str(output_template),
            youtube_url
        ], check=True)

        duration = cls.get_audio_duration(str(final_mp3))
        return str(final_mp3), duration

    @classmethod
    def get_audio_duration(cls, file_path: str) -> int:
        result = subprocess.run([
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ], capture_output=True, text=True, check=True)

        return int(float(result.stdout.strip()))

    @classmethod
    def create_clip(cls, source_file: str, start_time: int, duration: int) -> str:
        cls.ensure_directories()

        clip_id = str(uuid.uuid4())
        clip_path = cls.CLIPS_DIR / f"{clip_id}.mp3"

        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", source_file,
            "-ss", str(start_time),
            "-t", str(duration),
            "-acodec", "mp3",
            str(clip_path)
        ], check=True)

        return str(clip_path)

    @classmethod
    def validate_clip_bounds(cls, track_duration: int, start_time: int, duration: int):
        if start_time < 0:
            raise ValueError("start_time doit être >= 0")

        if duration <= 0:
            raise ValueError("duration doit être > 0")

        if start_time + duration > track_duration:
            raise ValueError("Le clip dépasse la durée totale du morceau")