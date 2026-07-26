# Product Spec

This is a living specification for the project. It should describe what the
system does, which features matter most, and what each feature must support.

## Product Direction

The long-term direction is a local-first home intelligence platform. The current
MVP is focused on a smart camera module, but future versions may include broader
home monitoring, alerts, accounts, permissions, and smart-home integrations.

## Current MVP

The current system supports:

- Live webcam streaming in the browser
- Backend health checks
- Camera availability testing
- Face detection on the live stream
- Basic local face recognition labels
- Configurable face match threshold
- Recognition label smoothing across recent frames
- Basic local login protection
- Basic motion detection stats
- 5-second rolling pipeline FPS metrics
- System health status derived from pipeline checks
- Persistent local motion and face events
- Event history page with simple filters
- Local snapshots for saved motion and face events
- Local suspicious-activity alert events
- Live dashboard alert indicator
- Local browser notifications for new suspicious alerts
- Protected known-face loading debug endpoint
- Recognition debug page for scores, thresholds, and label reasons

The current system does not yet include:

- Role-based permissions
- Cloud database storage
- Searchable long-term event analytics
- Cloud deployment
- Mobile apps
- Smart-home device control

## Priority Levels

- `P0`: Current MVP or must keep working
- `P1`: Next improvements
- `P2`: Planned after the MVP is stable
- `P3`: Future expansion

## Feature Priorities

| Priority | Feature | Status | Summary |
| --- | --- | --- | --- |
| P0 | Live camera view | Working | Browser-based live stream from the local webcam. |
| P0 | Face detection | Working | Detect faces and draw boxes on the stream. |
| P0 | Basic recognition labels | Working | Label known faces and unknown faces locally. |
| P1 | Basic activity signal | Started | Detect frame-to-frame motion and expose stats locally. |
| P1 | Local event history | Started | Store local motion, face, and alert events in SQLite with filters, snapshots, cooldowns, and retention cleanup. |
| P1 | Recognition quality | Started | Improve stability using multiple photos, thresholds, debug visibility, and smoothing. |
| P1 | Dashboard experience | Started | Show live camera, face, label, and motion status around the stream. |
| P1 | Pipeline observability | Started | Track FPS, uptime, and derived system health status. |
| P2 | Activity analysis | Planned | Turn basic motion signals into useful events over time. |
| P2 | Accounts and permissions | Planned | Add admin and lower-privilege user roles when remote or shared access is needed. |
| P2 | Local browser alert notifications | Started | Notify open browser sessions when new suspicious alerts are created. |
| P3 | Smart-home integrations | Future | Connect events to smart-home devices after safety rules are defined. |

## Feature Specs

### Live Camera View

Goal:
Show a reliable local live stream from the computer camera.

Requirements:

- Stream video through the backend.
- Keep `/video`, `/health`, and `/camera-test` working.
- Handle camera access failures with clear logs.

Acceptance criteria:

- The app opens at `http://localhost:8000`.
- The live stream appears in the browser.
- `/camera-test` reports whether a camera is available.

### Face Recognition Quality

Goal:
Improve recognition accuracy and reduce label flickering.

Requirements:

- Support multiple reference photos per person.
- Compare faces using stable embeddings.
- Expose a protected debug endpoint for loaded known-face labels and counts.
- Expose a protected debug page for recent raw and smoothed recognition results.
- Tune confidence thresholds from local environment settings.
- Smooth recognition labels across several frames.

Acceptance criteria:

- Known people are recognized more consistently.
- Unknown people remain labeled as `Anonymous`.
- `/known-faces` shows source image counts and loaded embedding counts.
- `/recognition-debug` shows current raw score, smoothed label, and reason.
- `FACE_MATCH_THRESHOLD` can be adjusted in `.env` without code changes.
- One weak frame should not immediately flip a stable known label to `Anonymous`.
- Recognition settings are easy to tune during testing.

### Dashboard Experience

Goal:
Make the live system easier to understand and operate.

Requirements:

- Keep the live view as the primary experience.
- Show camera and recognition status clearly.
- Show the current motion status clearly.
- Show the latest suspicious alert clearly.
- Allow local browser notifications for new suspicious alerts.
- Present known and anonymous labels in a readable way.
- Work well on desktop and mobile screens.

Acceptance criteria:

- Users can tell whether the camera is connected.
- Users can tell whether recognition is active.
- Users can tell when suspicious activity was detected.
- Users can enable browser notifications from the live dashboard.
- UI changes do not break the live stream.

### Pipeline Observability

Goal:
Make camera performance visible enough to debug and explain.

Requirements:

- Track camera FPS.
- Track stream FPS.
- Track face-analysis FPS.
- Track motion-processing FPS.
- Track skipped-analysis FPS.
- Derive a simple system status from pipeline metrics.
- Show these metrics through `/stats` and `/recognition-debug`.
- Expose the status through `/api/system-status`.
- Expose readable diagnostics and recommendations through `/api/diagnostics`.
- Record a local `system` event when the overall status changes.

Acceptance criteria:

- `/stats` returns 5-second rolling performance metrics.
- `/api/system-status` returns `healthy`, `idle`, `degraded`, or `error`.
- `/diagnostics` explains which pipeline stage needs attention.
- Status changes such as `healthy -> degraded` appear in event history.
- `/recognition-debug` shows the same metrics while the live stream is open.
- Metrics make it clear whether the camera, streaming, or analysis stage is slow.

### Basic Activity Signal

Goal:
Create a simple foundation for movement analysis without alerts or databases.

Requirements:

- Compare consecutive camera frames.
- Ignore small camera noise.
- Expose current motion status in `/stats`.
- Keep `/video`, `/health`, and `/camera-test` working.

Acceptance criteria:

- `/stats` shows whether motion is currently active.
- `/stats` includes a motion score and changed-area value.
- Motion settings can be tuned locally from `.env`.

### Local Event History

Goal:
Show recent camera activity using a local database that does not require a
database server.

Requirements:

- Record an event when motion starts.
- Record an event when a detected face label appears.
- Store events locally in SQLite.
- Expose the latest events through `/stats`.
- Expose filterable events through `/api/events`.
- Show the latest events in the frontend.
- Show a dedicated event history page.
- Save a local JPEG snapshot when an event is recorded.
- Apply simple cooldowns so repeated events do not flood the dashboard.
- Create a local alert event when motion and an anonymous face happen close together.
- Keep the local event database bounded by count and age settings.

Acceptance criteria:

- The dashboard shows recent motion, face, alert, and system events.
- The history page can filter by all, motion, face, alert, or system events.
- The history page shows snapshots when they are available.
- The history page can show local alert events.
- The same event type does not repeat too quickly when detection flickers.
- Events survive backend restarts.
- Old events are cleaned up according to local retention settings.
- No cloud storage, external notification service, or remote database is added yet.

### Accounts And Permissions

Goal:
Define controlled access when the project grows beyond a local-only demo.

Future roles:

- Admin: manage cameras, known people, settings, users, and alerts.
- Standard user: view allowed camera streams and receive relevant alerts.
- Viewer or guest: limited access to live status or approved views only.

Requirements to define later:

- Authentication method
- Permission model
- User management flow
- Privacy and audit requirements

Acceptance criteria:

- No account system is added until the team agrees it is needed.
- Permission rules are documented before implementation starts.

### Local Browser Alert Notifications

Goal:
Notify users about suspicious activity while the local dashboard is open.

Requirements:

- Reuse local alert events.
- Ask for browser notification permission from the live dashboard.
- Send one browser notification per new alert.
- Do not repeat notifications for old alerts already visible on page load.
- Avoid noisy or excessive alerts.
- Do not add cloud push notifications yet.

Acceptance criteria:

- Browser notifications can be enabled from the live dashboard.
- New suspicious alerts trigger a browser notification when permission is granted.
- Existing historical alerts do not trigger a notification on page load.
- Event storage avoids unnecessary personal or biometric data.

## Open Questions

- What product name should we use if the project expands beyond cameras?
- Which features require accounts before they are safe to use?
- Which data should stay local only?
- What accuracy level is acceptable before alerts are enabled?
- Which smart-home integrations are useful and safe for the first version?
