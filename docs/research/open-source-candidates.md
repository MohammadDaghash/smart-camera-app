# Open Source Candidates

Checked on: 2026-07-02

This note lists public repositories that may help the Smart Camera App. The current recommendation is to study and selectively reuse ideas or dependencies, not fork a full application yet. Forking a large project now would likely slow the MVP down and make our architecture harder to control.

## Recommendation

Start with a small technical spike for VidGear.

VidGear is focused on video capture and processing, which matches our current pain point: stable webcam streaming. It is much smaller than a full NVR/security platform and has an Apache-2.0 license, so it is a reasonable candidate to test as a dependency.

## Candidate Repositories

| Repository | License | Why It Matters | Recommendation |
| --- | --- | --- | --- |
| [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) | MIT | Mature local NVR with real-time object detection and camera/event architecture. | Use as an architecture reference only. Do not fork into the MVP. |
| [abhiTronix/vidgear](https://github.com/abhiTronix/vidgear) | Apache-2.0 | Python video processing framework with camera capture helpers that may improve stream stability. | Best first spike candidate. Test CamGear against our current OpenCV capture. |
| [SthPhoenix/InsightFace-REST](https://github.com/SthPhoenix/InsightFace-REST) | Apache-2.0 | FastAPI-based InsightFace service with deployment ideas for face recognition APIs. | Use as a reference if we later split recognition into a separate service. |
| [deepinsight/insightface](https://github.com/deepinsight/insightface) | Code is MIT; pretrained models have non-commercial/research restrictions | Strong face analysis library and model ecosystem. | Useful for research, but review model licensing before product use. |
| [Fairoos-palakkal/sentryid-Real-time-Face-Recognition-Surveillance-Intelligent-Access-Control-System](https://github.com/Fairoos-palakkal/sentryid-Real-time-Face-Recognition-Surveillance-Intelligent-Access-Control-System) | No clear license detected | Similar product direction: real-time face recognition, tracking, and dashboard concepts. | Reference ideas only. Do not copy code without a license. |
| [ruhyadi/vision-fr](https://github.com/ruhyadi/vision-fr) | No clear license detected | FastAPI plus face embeddings and vector search concepts. | Reference ideas only. Do not copy code without a license. |

## Engineering Rules For Reuse

- Prefer dependencies with clear licenses.
- Do not copy code from repositories with no license.
- Keep our app small and understandable.
- Add one external dependency at a time.
- Every dependency spike must include a rollback path.
- Any ML model must be checked for commercial/product licensing before adoption.

## Proposed Next Spike

Title: Evaluate VidGear for camera capture stability

Linear issue: [MOH-30](https://linear.app/mohammaddaghash/issue/MOH-30/spike-evaluate-vidgear-for-camera-capture-stability)

Goal:
Compare our current OpenCV `VideoCapture` webcam pipeline with VidGear `CamGear`.

Acceptance criteria:

- `/video`, `/health`, and `/camera-test` still work.
- Current OpenCV behavior is documented.
- VidGear behavior is tested locally on the laptop webcam.
- We record whether VidGear improves frame stability, startup reliability, or frame-read errors.
- No permanent app behavior change is merged unless the spike proves a clear benefit.
