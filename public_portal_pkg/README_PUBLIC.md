# Public Candidate Portal (drop-in package)

This package adds a **minimal public-facing flow** for external candidates:
- Public job pages (`/jobs`, `/jobs/<id>`)
- Auth (email-only) for candidates
- Apply page with **CV upload**
- Submission writes to your existing `Application` table and calls `run_cv_scoring(app_id)` if available
- Clean, navless, branded theme

## Install

1) Copy the contents of this folder into your app root (or unzip in place).  
Ensure these new folders exist:
```
templates_public/
static_public/
public.py
```

2) In your `app.py`:
```python
from public import public_bp
app.register_blueprint(public_bp)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")  # session for candidate auth
```

3) Ensure your models and `engine` are importable from `public.py`:
- `Application`, `Candidate`, `Job` (required)
- Optional: `Shortlist`, `TrustIDCheck`, `ESigRequest`

4) (Optional) Provide a helper:
```python
def run_cv_scoring(application_id: int):
    # Implement or reuse your internal CV scoring
    ...
```

5) Run your app and visit `/jobs` or share `/jobs/<id>` links publicly.

## Notes
- Auth is email-only for now (no password) to keep the flow lightweight. You can replace with password/magic-link later.
- CV files save under `static/uploads/cvs/`.
- All public templates extend `public_base.html` which carries the brand look without internal nav.
