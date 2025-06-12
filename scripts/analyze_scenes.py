import cv2
import os
import sys

def analyze_video_scenes(video_path, threshold=30.0, min_scene_duration=1.0):
    """
    Analyzes a video file to detect scene changes.

    Args:
        video_path (str): Path to the video file.
        threshold (float): Frame difference threshold to detect a scene change.
        min_scene_duration (float): Minimum duration in seconds for a scene to be considered.

    Returns:
        list: A list of tuples, where each tuple is (start_time, end_time) in seconds for a detected scene.
    """
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # Instead of raising FileNotFoundError directly, print and return empty list
            # as per original plan, though FileNotFoundError is more Pythonic for library functions.
            # For this exercise, sticking to the print and return empty list.
            print(f"Error: Video file not found or could not be opened: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        # Handle cases where fps might not be available or is zero.
        if fps == 0:
            print(f"Warning: Video FPS is 0 for '{video_path}'. Defaulting to 30 FPS. Scene timings might be inaccurate.")
            fps = 30.0 # Default FPS
        # else: # No need for else print here, too verbose for non-debug
            pass

        min_scene_frames = int(min_scene_duration * fps)

        scenes = []
        prev_frame_gray = None
        scene_start_frame_index = 0 # Use index for clarity
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break  # End of video

            current_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame_gray is not None:
                # Calculate Mean Squared Error (MSE) between current and previous frame's grayscale representation
                mse = ((prev_frame_gray.astype("float") - current_frame_gray.astype("float")) ** 2).mean()

                # If MSE exceeds the threshold, a potential scene change is detected
                if mse > threshold:
                    current_segment_duration_frames = frame_index - scene_start_frame_index
                    # Ensure the detected scene meets the minimum duration
                    if current_segment_duration_frames >= min_scene_frames:
                        start_time = scene_start_frame_index / fps
                        end_time = frame_index / fps # Current frame marks the end of the previous scene
                        scenes.append((start_time, end_time))
                    # The current frame (frame_index) is the beginning of the new scene
                    scene_start_frame_index = frame_index # Original position

            prev_frame_gray = current_frame_gray
            frame_index += 1

        # After the loop, add the last scene if it meets minimum duration
        # (frame_index now represents total frames)
        last_segment_duration_frames = frame_index - scene_start_frame_index
        if last_segment_duration_frames >= min_scene_frames:
            start_time = scene_start_frame_index / fps
            end_time = frame_index / fps
            scenes.append((start_time, end_time))

    except FileNotFoundError as e: # This was intended to be caught by cap.isOpened logic
        print(f"Error: Video file not found or could not be opened: {video_path}")
        return []
    except cv2.error as e:
        print(f"OpenCV error processing video: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()

    return scenes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_scenes.py <video_file_path>")
        print("No video file provided. You might want to create a dummy video for testing.")
        # Example: How to create a dummy video for quick testing
        import numpy as np
        try:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            dummy_out = cv2.VideoWriter('dummy_video.avi', fourcc, 20.0, (100, 100)) # Corrected dummy video path
            for i in range(60): # 3 seconds, 2 scenes
                frame = np.zeros((100, 100, 3), dtype=np.uint8)
                if i < 30: # First scene (black)
                    pass
                else: # Second scene (white)
                    frame[:] = [255,255,255]
                dummy_out.write(frame)
            dummy_out.release()
            print("Created 'dummy_video.avi'. Run: python analyze_scenes.py dummy_video.avi")
        except Exception as e:
            print(f"Could not create dummy video: {e}. OpenCV and a codec like XVID might be needed.")
        sys.exit(1)

    video_file_path = sys.argv[1]

    if not os.path.isfile(video_file_path): # More robust check for file existence
        print(f"Error: The provided video file '{video_file_path}' does not exist or is not a file.")
        print("Usage: python analyze_scenes.py <video_file_path>")
        sys.exit(1)

    print(f"Analyzing scenes in video: {video_file_path}")
    # Using default threshold and min_scene_duration for this test
    detected_scenes = analyze_video_scenes(video_file_path)

    if detected_scenes:
        print("\nDetected scenes (start_time, end_time):")
        for i, (start, end) in enumerate(detected_scenes):
            print(f"  Scene {i+1}: {start:.2f}s - {end:.2f}s (Duration: {end-start:.2f}s)")
    else:
        print("No scenes detected or an error occurred during analysis.")
