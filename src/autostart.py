import os
import sys
import platform
import subprocess
from pathlib import Path

LABEL = "com.wolfgangheis.socialagent"
DAY_NAMES = {1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT", 7: "SUN"}


def _plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _executable() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def _script() -> str:
    if getattr(sys, "frozen", False):
        return ""
    return str(Path(__file__).parent.parent / "main.py")


def is_enabled() -> bool:
    if platform.system() == "Darwin":
        return _plist_path().exists()
    if platform.system() == "Windows":
        r = subprocess.run(["schtasks", "/Query", "/TN", LABEL], capture_output=True)
        return r.returncode == 0
    return False


def enable(days: list[int], hour: int, minute: int):
    if platform.system() == "Darwin":
        _enable_mac(days, hour, minute)
    elif platform.system() == "Windows":
        _enable_windows(days, hour, minute)


def disable():
    if platform.system() == "Darwin":
        p = _plist_path()
        if p.exists():
            subprocess.run(["launchctl", "unload", str(p)])
            p.unlink()
    elif platform.system() == "Windows":
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", LABEL])


def _enable_mac(days, hour, minute):
    intervals = "\n".join(
        f"        <dict>\n"
        f"            <key>Weekday</key><integer>{d}</integer>\n"
        f"            <key>Hour</key><integer>{hour}</integer>\n"
        f"            <key>Minute</key><integer>{minute}</integer>\n"
        f"        </dict>"
        for d in days
    )
    exe = _executable()
    script = _script()
    args = f"<string>{exe}</string>"
    if script:
        args += f"\n        <string>{script}</string>"
    workdir = str(Path(script).parent) if script else str(Path(exe).parent)
    logdir = Path.home() / "Library" / "Logs"

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        {args}
    </array>
    <key>StartCalendarInterval</key>
    <array>
{intervals}
    </array>
    <key>WorkingDirectory</key><string>{workdir}</string>
    <key>StandardOutPath</key><string>{logdir}/WolfgangSocialAgent.log</string>
    <key>StandardErrorPath</key><string>{logdir}/WolfgangSocialAgent.err</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>"""

    p = _plist_path()
    if p.exists():
        subprocess.run(["launchctl", "unload", str(p)], capture_output=True)
    p.write_text(plist)
    subprocess.run(["launchctl", "load", str(p)], check=True)


def _enable_windows(days, hour, minute):
    days_str = ",".join(DAY_NAMES[d] for d in days)
    exe = _executable()
    script = _script()
    task = f'"{exe}" "{script}"' if script else f'"{exe}"'
    subprocess.run([
        "schtasks", "/Create", "/F",
        "/TN", LABEL, "/TR", task,
        "/SC", "WEEKLY", "/D", days_str,
        "/ST", f"{hour:02d}:{minute:02d}",
    ], check=True)
