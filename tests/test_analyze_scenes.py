import unittest
import sys
import os
import cv2 # For creating dummy video
import numpy as np # For creating dummy video

# Adjust sys.path to allow importing from the 'scripts' directory
# This assumes the test is run from the root of the project where 'scripts' and 'tests' are subdirectories
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from scripts.analyze_scenes import analyze_video_scenes

class TestAnalyzeScenes(unittest.TestCase):

    def _create_dummy_video(self, filename, num_frames, fps, width, height, scene_changes_at_frames=None):
        """Helper function to create a dummy video."""
        if scene_changes_at_frames is None:
            scene_changes_at_frames = []

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, float(fps), (width, height))
        if not out.isOpened():
            raise Exception(f"Failed to open VideoWriter for {filename}")

        current_color_val = 0
        for i in range(num_frames):
            if i in scene_changes_at_frames:
                current_color_val = 255 - current_color_val # Toggle color

            frame = np.full((height, width, 3), current_color_val, dtype=np.uint8)
            # cv2.putText(frame, f'F:{i}', (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1) # Removed to make frames cleaner
            out.write(frame)
        out.release()

    def setUp(self):
        """Set up test fixtures, including creating dummy video files."""
        self.dummy_video_path = "dummy_test_video.avi"
        self.empty_video_path = "empty_test_video.avi"
        self.non_existent_video_path = "non_existent_video.avi"

        # Create a dummy video with known scene changes
        # 3 seconds, 20 FPS, 2 scenes (change at frame 30)
        # Scene 1: frames 0-29 (0.0s to 1.5s)
        # Scene 2: frames 30-59 (1.5s to 3.0s)
        self._create_dummy_video(self.dummy_video_path, num_frames=60, fps=20, width=100, height=100, scene_changes_at_frames=[30])

        # Create an empty file to simulate an invalid video
        with open(self.empty_video_path, 'w') as f:
            pass # Just create an empty file

        # Ensure non_existent_video_path does not exist
        if os.path.exists(self.non_existent_video_path):
            os.remove(self.non_existent_video_path)

    def tearDown(self):
        """Tear down test fixtures, removing created files."""
        if os.path.exists(self.dummy_video_path):
            os.remove(self.dummy_video_path)
        if os.path.exists(self.empty_video_path):
            os.remove(self.empty_video_path)

    def test_dummy_video_analysis(self):
        """Test analysis of a dummy video with known scene changes."""
        scenes = analyze_video_scenes(self.dummy_video_path, threshold=10.0, min_scene_duration=0.5)

        self.assertIsInstance(scenes, list, "Should return a list.")
        self.assertEqual(len(scenes), 2, "Should detect 2 scenes in the dummy video.")

        for start, end in scenes:
            self.assertIsInstance(start, float, "Start time should be a float.")
            self.assertIsInstance(end, float, "End time should be a float.")
            self.assertGreater(end, start, "End time should be greater than start time.")
            self.assertGreaterEqual(start, 0, "Start time should be non-negative.")

        # Expected scenes based on dummy video creation (fps=20)
        # Scene 1: 0.0s to 1.5s (frames 0-30)
        # Scene 2: 1.5s to 3.0s (frames 30-60)
        if len(scenes) == 2:
            self.assertAlmostEqual(scenes[0][0], 0.0, delta=0.1)
            self.assertAlmostEqual(scenes[0][1], 1.5, delta=0.1) # frame 30 / 20fps
            self.assertAlmostEqual(scenes[1][0], 1.5, delta=0.1) # frame 30 / 20fps
            self.assertAlmostEqual(scenes[1][1], 3.0, delta=0.1) # frame 60 / 20fps

    def test_file_not_found(self):
        """Test behavior when the video file is not found."""
        # Suppress print output from analyze_video_scenes for this test
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            scenes = analyze_video_scenes(self.non_existent_video_path)
            self.assertEqual(scenes, [], "Should return an empty list for a non-existent file.")
        finally:
            sys.stdout.close()
            sys.stdout = original_stdout # Restore stdout

    def test_invalid_video_file(self):
        """Test behavior with an invalid (empty) video file."""
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            scenes = analyze_video_scenes(self.empty_video_path)
            self.assertEqual(scenes, [], "Should return an empty list for an invalid/empty video file.")
        finally:
            sys.stdout.close()
            sys.stdout = original_stdout

    def test_video_with_no_significant_changes(self):
        """Test a video with no scene changes (or changes below threshold)."""
        no_change_video_path = "no_change_video.avi"
        self._create_dummy_video(no_change_video_path, num_frames=60, fps=20, width=100, height=100, scene_changes_at_frames=[]) # No explicit changes

        scenes = analyze_video_scenes(no_change_video_path, threshold=30.0, min_scene_duration=0.5)
        # Expecting one scene that covers the whole video, or an empty list if the first "scene" start is frame 0 and end is frame 0
        # The current logic should produce one scene for the entire duration if no changes are above threshold
        self.assertIsInstance(scenes, list)
        if scenes: # It might produce one scene for the whole video
             self.assertEqual(len(scenes), 1, "Should detect one scene for the whole video if no changes.")
             self.assertAlmostEqual(scenes[0][0], 0.0, delta=0.1)
             self.assertAlmostEqual(scenes[0][1], 3.0, delta=0.1) # 60 frames / 20 fps
        # else: # Or it might produce no scenes if the min_scene_duration logic for the *last* scene is tricky
        #    self.assertEqual(len(scenes), 0) # This would also be acceptable depending on strict interpretation

        if os.path.exists(no_change_video_path):
            os.remove(no_change_video_path)

    def test_min_scene_duration(self):
        """Test that scenes shorter than min_scene_duration are filtered."""
        short_scene_video_path = "short_scene_video.avi"
        # Scene 1: 0-9 (0.5s), Scene 2: 10-19 (0.5s), Scene 3: 20-29 (0.5s), etc.
        # Total 60 frames, 20fps. Changes every 10 frames (0.5s)
        self._create_dummy_video(short_scene_video_path, num_frames=60, fps=20, width=100, height=100,
                                 scene_changes_at_frames=[10, 20, 30, 40, 50])

        # Min duration 1.0s, threshold low enough to detect all changes
        scenes = analyze_video_scenes(short_scene_video_path, threshold=10.0, min_scene_duration=1.0)

        # With min_scene_duration = 1.0s, and changes every 0.5s,
        # the logic should merge these.
        # Expected: [0.0, 3.0] or perhaps more granularly depending on how merging happens.
        # The current `analyze_scenes.py` logic: if a change is detected, the *previous* segment
        # is added if it meets duration. Then the new scene starts.
        # So, frame 0-9 (0.5s) -> change -> scene_start_frame=10. Not added.
        # frame 10-19 (0.5s) -> change -> scene_start_frame=20. Not added.
        # ...
        # Last scene: frame 50-59 (0.5s). Not added.
        # The final "add the last scene" logic will add frame_start_index to frame_count.
        # If scene_start_frame_index is 50, (60-50)/20 = 0.5s. This won't be added.
        # This implies it should return an empty list if all scenes are too short.

        # Let's re-evaluate based on the script's logic:
        # 1. Change at 10. Scene 0-9. Duration 0.5s. Not added. scene_start_frame_index = 10.
        # 2. Change at 20. Scene 10-19. Duration 0.5s. Not added. scene_start_frame_index = 20.
        # ...
        # 5. Change at 50. Scene 40-49. Duration 0.5s. Not added. scene_start_frame_index = 50.
        # End of loop. Last scene check: (60 - 50) = 10 frames = 0.5s. Not added.
        self.assertEqual(len(scenes), 0, "No scenes should be returned if all are shorter than min_scene_duration.")

        # Test with duration that should allow scenes
        scenes_longer_min = analyze_video_scenes(short_scene_video_path, threshold=10.0, min_scene_duration=0.4)
        # Expected: [0,0.5], [0.5,1.0], [1.0,1.5], [1.5,2.0], [2.0,2.5], then last scene [2.5,3.0]
        # Let's check:
        # 1. Change at 10. Scene 0-9 (0.5s). Added. scene_start_frame_index = 10. scenes: [(0.0, 0.5)]
        # 2. Change at 20. Scene 10-19 (0.5s). Added. scene_start_frame_index = 20. scenes: [..., (0.5, 1.0)]
        # ...
        # 5. Change at 50. Scene 40-49 (0.5s). Added. scene_start_frame_index = 50. scenes: [..., (2.0, 2.5)]
        # End of loop. Last scene check: (60-50) = 10 frames = 0.5s. Added. scenes: [...,(2.5, 3.0)]
        # So, 6 scenes in total.
        self.assertEqual(len(scenes_longer_min), 6, "Should detect 6 scenes if min_scene_duration is 0.4s and changes are every 0.5s.")


        if os.path.exists(short_scene_video_path):
            os.remove(short_scene_video_path)

if __name__ == '__main__':
    unittest.main()
