import re
import sys
import subprocess
from helpers import print_message, PIP_PROXY, ERROR



_ANCHOR_RE = re.compile(
    r'<a\s+[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<name>[^<]+)</a>',
    re.IGNORECASE,
)


def process_package(package_line: str, pypi_url: str):
    match = _ANCHOR_RE.search(package_line)
    if not match:
        return None

    href = match.group("href")
    package_name = match.group("name").strip()
    if not href or not package_name:
        return None

    return {"package": package_name, "url": f"{pypi_url}{href}"}


def pip_install(package: str, version: str = None):
    package = package.strip()
    if not package:
        print_message("Package name is empty.", ERROR)
        return False

    command = [sys.executable, "-m", "pip", "install", package if not version else f"{package}=={version}"]

    if PIP_PROXY:
        command.extend(["--proxy", PIP_PROXY])

    try:
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        for line in iter(p.stdout.readline, b''):
            print(line.decode('utf-8'))
        p.stdout.close()
        p.wait()
        print_message(f"Successfully installed package '{package}'.")
        return True

    except subprocess.CalledProcessError as exc:
        error_text = (exc.stderr or exc.stdout or "").strip() or "Unknown pip error."
        print_message(
            f"Error during package installation for '{package}': {error_text}",
            ERROR,
        )
        return False
