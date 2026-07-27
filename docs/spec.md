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
- Event history page with type, label, and time filters
- Activity review page that groups and filters related local events
- Local snapshots for saved motion and face events
- Local suspicious-activity alert events
- Live dashboard alert indicator
- Live dashboard operational summary with review counts, alert state, FPS, and top action
- Local browser notifications for new suspicious alerts
- Protected known-face loading debug endpoint
- Recognition debug page for scores, thresholds, and label reasons
- Local ML evaluation toolkit for threshold and confusion-matrix reports
- Local recognition score history for confidence and threshold monitoring

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
| P1 | Activity review workflow | Started | Group, filter, and triage nearby raw events into reviewable incidents with severity, labels, timing, source event context, and saved status. |
| P1 | Recognition quality | Started | Improve stability using multiple photos, thresholds, debug visibility, score history, and smoothing. |
| P1 | ML evaluation toolkit | Started | Evaluate recognition thresholds using labeled images, metrics, and confusion matrices. |
| P1 | Dashboard experience | Started | Show live camera, face, label, motion, alert, review, FPS, and top-action status around the stream. |
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
- Store bounded local score observations for recognition confidence history.
- Tune confidence thresholds from local environment settings.
- Smooth recognition labels across several frames.

Acceptance criteria:

- Known people are recognized more consistently.
- Unknown people remain labeled as `Anonymous`.
- `/known-faces` shows source image counts and loaded embedding counts.
- `/recognition-debug` shows current raw score, smoothed label, and reason.
- `/recognition-metrics` shows local score history and per-label score summaries.
- `/api/recognition-metrics` exposes bounded local score observations.
- `FACE_MATCH_THRESHOLD` can be adjusted in `.env` without code changes.
- One weak frame should not immediately flip a stable known label to `Anonymous`.
- Recognition settings are easy to tune during testing.

### ML Evaluation Toolkit

Goal:
Measure recognition quality before changing production thresholds.

Requirements:

- Use labeled image folders for test data.
- Compare test embeddings against known-face embeddings.
- Sweep recognition thresholds.
- Report accuracy, precision, recall, macro F1, anonymous false positives, and
  known false-anonymous rates.
- Generate predictions CSV, score distribution CSV, per-label metrics CSV,
  threshold CSV, confusion matrix image, threshold plot, summary JSON, and a
  recommended threshold file.
- Keep personal evaluation images and generated reports local-only.

Acceptance criteria:

- The toolkit runs without webcam access.
- The toolkit can evaluate `Mohammad`, `Omar`, and `Anonymous` test folders.
- The output explains whether the current threshold is too strict or too loose.
- The generated CSV files can be opened in spreadsheet tools, Python notebooks,
  or MATLAB for further analysis.

### Dashboard Experience

Goal:
Make the live system easier to understand and operate.

Requirements:

- Keep the live view as the primary experience.
- Show camera and recognition status clearly.
- Show the current motion status clearly.
- Show the latest suspicious alert clearly.
- Show new review item counts clearly.
- Show camera FPS and stream/analysis FPS clearly.
- Show the top recommended local action clearly.
- Expose homepage summary data through `/api/dashboard-summary`.
- Allow local browser notifications for new suspicious alerts.
- Present known and anonymous labels in a readable way.
- Work well on desktop and mobile screens.

Acceptance criteria:

- Users can tell whether the camera is connected.
- Users can tell whether recognition is active.
- Users can tell when suspicious activity was detected.
- Users can tell how many new review items need attention.
- Users can see the current camera FPS and stream/analysis FPS.
- Users can open review, diagnostics, and history from the summary area.
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
- Track bounded recognition score observations.
- Derive a simple system status from pipeline metrics.
- Show these metrics through `/stats` and `/recognition-debug`.
- Expose the status through `/api/system-status`.
- Expose readable diagnostics and recommendations through `/api/diagnostics`.
- Show the top diagnostics recommendation on the live dashboard.
- Expose current non-secret tuning settings through `/api/settings`.
- Record a local `system` event when the overall status changes.

Acceptance criteria:

- `/stats` returns 5-second rolling performance metrics.
- `/api/system-status` returns `healthy`, `idle`, `degraded`, or `error`.
- `/diagnostics` explains which pipeline stage needs attention.
- The live dashboard shows the top recommended local action.
- `/settings` shows current face, motion, event, and alert tuning values.
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
- Filter event history by type, label, and time range.
- Save a local JPEG snapshot when an event is recorded.
- Apply simple cooldowns so repeated events do not flood the dashboard.
- Create a local alert event when motion and an anonymous face happen close together.
- Keep the local event database bounded by count and age settings.

Acceptance criteria:

- The dashboard shows recent motion, face, alert, and system events.
- The history page can filter by all, motion, face, alert, or system events.
- The history page can filter by known or anonymous label.
- The history page can filter by local start and end time.
- The history page shows snapshots when they are available.
- The history page can show local alert events.
- The same event type does not repeat too quickly when detection flickers.
- Events survive backend restarts.
- Old events are cleaned up according to local retention settings.
- No cloud storage, external notification service, or remote database is added yet.

### Activity Review Workflow

Goal:
Turn low-level event rows into reviewable activity items.

Requirements:

- Read recent local events from SQLite.
- Group nearby motion, face, alert, and system events by timestamp.
- Mark grouped items as `alert`, `detection`, or `info`.
- Include labels, event count, duration, and source event details.
- Filter review items by label and time range.
- Save review item status as `new`, `reviewed`, or `false_positive`.
- Show review items in a simple `/review` page.
- Expose review data through `/api/review`.
- Expose review status updates through `/api/review/{review_id}/status`.
- Keep the feature local-only and database-light for the MVP.

Acceptance criteria:

- `/review` shows grouped activity instead of only raw event rows.
- `/api/review` returns grouped items with severity, labels, timing, and events.
- Alert events make the whole review item severity `alert`.
- Face or motion-only groups become `detection`.
- System-only groups become `info`.
- Filtering a review item by label preserves related source events in the group.
- Review status can be changed from the `/review` page.
- Review status survives browser refreshes and backend restarts.
- The review grouping gap can be tuned from `.env`.

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
