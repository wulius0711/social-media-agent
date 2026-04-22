import base64
import requests


DAY_NAMES = {0: "Sonntag", 1: "Montag", 2: "Dienstag", 3: "Mittwoch",
             4: "Donnerstag", 5: "Freitag", 6: "Samstag"}

# Vienna is UTC+1 (winter) / UTC+2 (summer). We use UTC+1 as safe default.
_VIENNA_OFFSET = 1


def days_and_hour_to_cron(days: list[int], hour_vienna: int, minute: int = 0) -> list[str]:
    """Convert Vienna local time to UTC cron expressions, one per day."""
    hour_utc = (hour_vienna - _VIENNA_OFFSET) % 24
    return [f"{minute} {hour_utc} * * {d}" for d in days]


def build_workflow_yaml(days: list[int], hour_vienna: int, minute: int = 0) -> str:
    crons = days_and_hour_to_cron(days, hour_vienna, minute)
    schedule_lines = "\n".join(
        f'    - cron: "{c}"  # {DAY_NAMES[d]} {hour_vienna:02d}:{minute:02d} Wien'
        for c, d in zip(crons, days)
    )
    return f"""name: Social Media Post

on:
  schedule:
{schedule_lines}
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run agent
        env:
          OPENAI_API_KEY:            ${{{{ secrets.OPENAI_API_KEY }}}}
          IMGBB_API_KEY:             ${{{{ secrets.IMGBB_API_KEY }}}}
          CLOUDINARY_CLOUD_NAME:     ${{{{ secrets.CLOUDINARY_CLOUD_NAME }}}}
          CLOUDINARY_API_KEY:        ${{{{ secrets.CLOUDINARY_API_KEY }}}}
          CLOUDINARY_API_SECRET:     ${{{{ secrets.CLOUDINARY_API_SECRET }}}}
          LINKEDIN_ACCESS_TOKEN:     ${{{{ secrets.LINKEDIN_ACCESS_TOKEN }}}}
          LINKEDIN_AUTHOR_URN:       ${{{{ secrets.LINKEDIN_AUTHOR_URN }}}}
          INSTAGRAM_USER_ID:         ${{{{ secrets.INSTAGRAM_USER_ID }}}}
          INSTAGRAM_ACCESS_TOKEN:    ${{{{ secrets.INSTAGRAM_ACCESS_TOKEN }}}}
          BUSINESS_NAME:             ${{{{ secrets.BUSINESS_NAME }}}}
          BUSINESS_DESCRIPTION:      ${{{{ secrets.BUSINESS_DESCRIPTION }}}}
          BUSINESS_TARGET:           ${{{{ secrets.BUSINESS_TARGET }}}}
          BUSINESS_TONE_HINTS:       ${{{{ secrets.BUSINESS_TONE_HINTS }}}}
          BUSINESS_LANGUAGE:         ${{{{ secrets.BUSINESS_LANGUAGE }}}}
          POST_LINKEDIN:             ${{{{ secrets.POST_LINKEDIN }}}}
          POST_INSTAGRAM:            ${{{{ secrets.POST_INSTAGRAM }}}}
          GENERATE_IMAGE:            ${{{{ secrets.GENERATE_IMAGE }}}}
          POST_LENGTH:               ${{{{ secrets.POST_LENGTH }}}}
          POST_TONE:                 ${{{{ secrets.POST_TONE }}}}
          HASHTAG_COUNT:             ${{{{ secrets.HASHTAG_COUNT }}}}
        run: python main.py
"""


def update_github_schedule(
    gh_token: str,
    repo_full: str,
    days: list[int],
    hour_vienna: int,
    minute: int = 0,
) -> bool:
    """Push updated workflow YAML to GitHub. Returns True on success."""
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    path = ".github/workflows/post.yml"
    url = f"https://api.github.com/repos/{repo_full}/contents/{path}"

    # Get current file SHA
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    sha = r.json()["sha"]

    new_content = build_workflow_yaml(days, hour_vienna, minute)
    encoded = base64.b64encode(new_content.encode()).decode()

    day_str = ", ".join(DAY_NAMES[d] for d in days)
    r2 = requests.put(url, headers=headers, json={
        "message": f"Update posting schedule: {day_str} {hour_vienna:02d}:{minute:02d}",
        "content": encoded,
        "sha": sha,
    }, timeout=15)
    r2.raise_for_status()
    return True
