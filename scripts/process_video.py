import sys
import os
import json
import subprocess
import uuid
import tempfile
import shutil

def run_ffmpeg_command(command_parts):
    """
    Executes an ffmpeg command using subprocess.run and checks for errors.
    Prints stdout/stderr if issues occur. Returns True on success, False on failure.
    """
    try:
        # print(f"Running FFmpeg command: {' '.join(command_parts)}", file=sys.stderr) # Optional: for debugging
        process = subprocess.run(command_parts, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            print(f"Error executing FFmpeg command: {' '.join(command_parts)}", file=sys.stderr)
            print(f"FFmpeg stdout:\n{process.stdout}", file=sys.stderr)
            print(f"FFmpeg stderr:\n{process.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Exception during FFmpeg command execution: {e}", file=sys.stderr)
        print(f"Command was: {' '.join(command_parts)}", file=sys.stderr)
        return False

def process_video(input_path, scenes_json_str, output_dir_base):
    """
    Processes a video by extracting scenes, concatenating them, formatting for 9:16, and trimming.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input video path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    try:
        scenes = json.loads(scenes_json_str)
        if not isinstance(scenes, list) or not all(isinstance(s, list) and len(s) == 2 for s in scenes):
            raise ValueError("Scenes JSON must be a list of [start, end] pairs.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing scenes JSON: {e}", file=sys.stderr)
        print(f"Received: {scenes_json_str}", file=sys.stderr)
        sys.exit(1)

    if not scenes:
        print("Error: No scenes provided to process.", file=sys.stderr)
        sys.exit(1)

    temp_dir = tempfile.mkdtemp(prefix="ffmpeg_clips_", dir="/tmp")
    clip_paths = []
    success = True

    print(f"Using temporary directory: {temp_dir}", file=sys.stderr)

    for i, scene in enumerate(scenes):
        start_time = scene[0]
        end_time = scene[1]
        duration = end_time - start_time
        if duration <= 0:
            print(f"Warning: Skipping scene {i+1} due to invalid duration (start: {start_time}, end: {end_time}).", file=sys.stderr)
            continue

        clip_filename = os.path.join(temp_dir, f"clip_{i+1}.mp4")

        # Using -c copy can be problematic for precise cuts if not on I-frames.
        # For better precision, re-encoding might be needed: e.g. -c:v libx264 -c:a aac
        # However, -c copy is much faster. Let's try with it first.
        # If cuts are inaccurate, change to:
        # cmd_extract = [
        #     "ffmpeg", "-y", "-i", input_path,
        #     "-ss", str(start_time), "-to", str(end_time),
        #     "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        #     "-c:a", "aac", "-b:a", "128k",
        #     clip_filename
        # ]
        cmd_extract = [
            "ffmpeg", "-y", # Overwrite output files without asking
            "-i", input_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy", # Fast, but potentially inaccurate cuts
            # "-avoid_negative_ts", "make_zero", # May help with timestamp issues from -c copy
            "-map_metadata", "-1", # Avoids issues with metadata from source video
            clip_filename
        ]
        if run_ffmpeg_command(cmd_extract):
            # Verify clip was created and has size (ffmpeg can succeed but create empty file if -to is before -ss for -c copy with some source files)
            if os.path.exists(clip_filename) and os.path.getsize(clip_filename) > 100: # Check if > 100 bytes
                 clip_paths.append(clip_filename)
            else:
                print(f"Warning: Extracted clip {clip_filename} is empty or too small. Trying re-encode.", file=sys.stderr)
                cmd_extract_reencode = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-ss", str(start_time), "-to", str(end_time),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-map_metadata", "-1",
                    clip_filename
                ]
                if run_ffmpeg_command(cmd_extract_reencode):
                    if os.path.exists(clip_filename) and os.path.getsize(clip_filename) > 100:
                        clip_paths.append(clip_filename)
                    else:
                        print(f"Error: Re-encoded clip {clip_filename} is still empty or too small. Skipping.", file=sys.stderr)
                        success = False # Mark as partial failure if one clip fails
                else:
                    success = False
        else:
            success = False # Mark as partial failure

    if not clip_paths:
        print("Error: No clips were successfully extracted.", file=sys.stderr)
        shutil.rmtree(temp_dir)
        sys.exit(1)

    file_list_path = os.path.join(temp_dir, "file_list.txt")
    with open(file_list_path, 'w') as f:
        for path in clip_paths:
            # FFmpeg concat demuxer requires relative paths from the list file if -safe 0 is not used,
            # or absolute paths if -safe 0 is used. Using absolute for simplicity with -safe 0.
            f.write(f"file '{os.path.abspath(path)}'\n")

    unique_filename = f"{uuid.uuid4()}_reel.mp4"
    final_output_path = os.path.join(output_dir_base, unique_filename)

    # Ensure output directory exists
    os.makedirs(output_dir_base, exist_ok=True)

    # Filter complex for 9:16 aspect ratio:
    # scale=w=540:h=960:force_original_aspect_ratio=decrease will scale down to fit within 540x960.
    # pad=540:960:(ow-iw)/2:(oh-ih)/2 will add black bars to fill 540x960.
    # setsar=1 ensures correct pixel aspect ratio.
    vf_complex = "scale=w=540:h=960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2,setsar=1"

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0", # Allows absolute paths in file_list.txt
        "-i", file_list_path,
        "-vf", vf_complex,
        "-t", "60", # Trim final output to 60 seconds
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        final_output_path
    ]

    if not run_ffmpeg_command(cmd_concat):
        print("Error: Failed to concatenate and format video.", file=sys.stderr)
        success = False # Overall process failed if concat fails

    print(f"Cleaning up temporary directory: {temp_dir}", file=sys.stderr)
    shutil.rmtree(temp_dir)

    if success and os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 0:
        print(final_output_path) # Print the final output path to stdout for n8n
    else:
        print("Error: Final output reel not created successfully or is empty.", file=sys.stderr)
        if os.path.exists(final_output_path): # remove empty/failed output
            os.remove(final_output_path)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python process_video.py <input_video_path> <scenes_json_string> <output_dir_base>", file=sys.stderr)
        print("Example: python process_video.py /path/to/video.mp4 '[[0,5],[10,15]]' /app/output", file=sys.stderr)
        sys.exit(1)

    input_video = sys.argv[1]
    scenes_data = sys.argv[2]
    output_directory = sys.argv[3] # This should be like /app/output

    process_video(input_video, scenes_data, output_directory)
