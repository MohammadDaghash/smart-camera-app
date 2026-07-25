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
- Basic local login protection
- Basic motion detection stats

The current system does not yet include:

- Role-based permissions
- Databases or event history
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
| P1 | Recognition quality | Planned | Improve stability using multiple photos, thresholds, and smoothing. |
| P1 | Dashboard experience | Started | Show live camera, face, label, and motion status around the stream. |
| P2 | Activity analysis | Planned | Turn basic motion signals into useful events over time. |
| P2 | Accounts and permissions | Planned | Add admin and lower-privilege user roles when remote or shared access is needed. |
| P2 | Alerts and event history | Planned | Store important events and notify users about suspicious activity. |
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
- Tune confidence thresholds.
- Smooth recognition labels across several frames.

Acceptance criteria:

- Known people are recognized more consistently.
- Unknown people remain labeled as `Anonymous`.
- Recognition settings are easy to tune during testing.

### Dashboard Experience

Goal:
Make the live system easier to understand and operate.

Requirements:

- Keep the live view as the primary experience.
- Show camera and recognition status clearly.
- Show the current motion status clearly.
- Present known and anonymous labels in a readable way.
- Work well on desktop and mobile screens.

Acceptance criteria:

- Users can tell whether the camera is connected.
- Users can tell whether recognition is active.
- UI changes do not break the live stream.

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

### Alerts And Event History

Goal:
Help users understand important activity without watching the camera constantly.

Future requirements:

- Detect important events.
- Store event time, type, and confidence.
- Notify users only when confidence and safety rules are satisfied.
- Avoid noisy or excessive alerts.

Acceptance criteria:

- Alert rules are documented before any notification system is added.
- Event storage avoids unnecessary personal or biometric data.

## Open Questions

- What product name should we use if the project expands beyond cameras?
- Which features require accounts before they are safe to use?
- Which data should stay local only?
- What accuracy level is acceptable before alerts are enabled?
- Which smart-home integrations are useful and safe for the first version?
