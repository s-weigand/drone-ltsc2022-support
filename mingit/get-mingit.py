# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "rich",
# ]
# ///
from pathlib import Path
import httpx
import os
from zipfile import ZipFile
from io import BytesIO
from typing import IO, Any
from dotenv import load_dotenv

from rich.console import Console

load_dotenv()
USE_CACHE = "CI" not in os.environ
HERE = Path(__file__).parent
REPO_ROOT = HERE.parent
CACHE_DIR = REPO_ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

EXTRACT_DIR = HERE / "mingit-files"
EXTRACT_DIR.mkdir(exist_ok=True)


EXTRA_HEADERS = {}
# Needed for CI rate limits
gh_token = os.getenv("GH_TOKEN")
if gh_token is not None:
    EXTRA_HEADERS["Authorization"] = f"Bearer {gh_token}"

console = Console(force_terminal=True)


def fetch_latest_release_assets(orga: str, repo: str) -> str:
    """Fetch the bundle download url for the release with tag ``WINGET_VERSION``."""
    resp = httpx.get(
        f"https://api.github.com/repos/{orga}/{repo}/releases", headers=EXTRA_HEADERS
    )
    resp.raise_for_status()
    for release in resp.json():
        if release.get("prerelease", None) is False:
            console.print(
                f"[blue]Found latest release for [green]{orga}/{repo}[/green]: "
                f"[dark_violet]{release['tag_name']}"
            )
            return release["assets"]
    msg = "API response has unexpected shape."
    raise ValueError(msg)


def filter_assets(assets: list[dict[str, Any]], name_contains: list[str]) -> str:
    for asset in assets:
        if all(
            substring.lower() in asset["name"].lower() for substring in name_contains
        ):
            dl_url = asset["browser_download_url"]
            console.print(
                f"[blue]Found download url using [green]{name_contains=}[/green]:\n"
                f"\t[dark_violet]{dl_url}"
            )
            return dl_url


def create_bundle_buffer(download_url: str) -> IO[bytes]:
    """Create buffer of the bundle either from cache or download."""
    file_name = download_url.rsplit("/")[-1]
    cache_file = CACHE_DIR / file_name
    if USE_CACHE is True and cache_file.is_file() is True:
        console.print(
            f"[blue]Using cached bundle: [dark_violet]{cache_file.as_posix()}"
        )
        return BytesIO(cache_file.read_bytes())
    console.print(f"[yellow] Downloading new bundle from [dark_violet]{download_url}")
    resp = httpx.get(download_url, follow_redirects=True, headers=EXTRA_HEADERS)
    resp.raise_for_status()
    if USE_CACHE is True:
        cache_file.write_bytes(resp.content)
    return BytesIO(resp.content)


def extract_bundle(zip_buffer: IO[bytes], location: Path, *, nested: bool = False):
    with ZipFile(zip_buffer) as outer_zip:
        if nested is False:
            outer_zip.extractall(location)
        else:
            for item in outer_zip.infolist():
                _, _, new_filename = item.filename.partition("/")
                if new_filename == "":
                    continue
                item.filename = new_filename
                outer_zip.extract(item, location)


def get_files(
    *,
    orga: str,
    repo: str,
    name_contains: list[str],
    extract_location: Path,
    nested_zip: bool = False,
):
    assets = fetch_latest_release_assets(orga, repo)
    dl_url = filter_assets(assets, name_contains)
    bundle_buffer = create_bundle_buffer(dl_url)
    extract_bundle(bundle_buffer, extract_location, nested=nested_zip)


def main() -> None:
    """Extract files minimal required files to run the winget cli"""
    get_files(
        orga="git-for-windows",
        repo="git",
        name_contains=["mingit", "64-bit.zip"],
        extract_location=EXTRACT_DIR,
    )
    get_files(
        orga="git-lfs",
        repo="git-lfs",
        name_contains=["windows", "amd64", ".zip"],
        extract_location=EXTRACT_DIR / "usr/bin",
        nested_zip=True,
    )


if __name__ == "__main__":
    main()
