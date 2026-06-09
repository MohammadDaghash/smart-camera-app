# Suggested GitHub Issues

## Omar

### Issue: Refine backend camera pipeline boundaries

Description:
Review the `backend/app/services/camera_service.py` module and make sure camera opening, reconnection, frame reads, and stream cleanup are safe and maintainable.

Acceptance criteria:

- Camera access logic remains isolated from route handlers.
- Camera resources are always released on stream close.
- `/camera-test` still reports the working camera index.
- `/video` still streams MJPEG frames.
- Any pipeline changes are documented in `backend/README.md`.

### Issue: Add backend route and service review checklist

Description:
Create a small checklist for backend pull requests covering route shape, service boundaries, logging, and camera resource safety.

Acceptance criteria:

- Checklist is added to `docs/git-workflow.md` or a pull-request template.
- Checklist includes route, service, logging, and resource cleanup items.
- The team agrees to use the checklist before merging into `dev`.

## Mohammad

### Issue: Support multiple known-face photos per person

Description:
Upgrade known-face loading from one image per person to folders containing multiple images per person. Average embeddings for each person to improve recognition stability.

Acceptance criteria:

- Supports structure such as `known_faces/Mohammad/1.jpg`.
- Existing flat files still work or a migration path is documented.
- Logs show how many photos were loaded per person.
- Recognition uses averaged embeddings.
- Personal photos remain ignored by Git.

### Issue: Add recognition smoothing across frames

Description:
Reduce frame-to-frame label flicker by requiring consistent recognition over several frames before displaying a known label.

Acceptance criteria:

- Labels do not switch every frame.
- Unknown faces still show `Anonymous`.
- Smoothing parameters are easy to tune.
- Logs include useful confidence information during testing.

## Majd

### Issue: Build a simple frontend dashboard shell

Description:
Improve the frontend from a single live-view page into a small dashboard while keeping the video stream as the primary experience.

Acceptance criteria:

- Live stream remains visible at `http://localhost:8000`.
- Dashboard shows camera status.
- Dashboard shows recognition status text.
- UI stays simple and does not require React yet unless the team agrees.

### Issue: Improve video overlay and status presentation

Description:
Design clearer visual feedback for labels, camera status, and anonymous faces.

Acceptance criteria:

- Status text is visible and readable.
- Unknown faces are visually distinct from known faces.
- Mobile layout remains usable.
- No frontend changes break `/video`.
