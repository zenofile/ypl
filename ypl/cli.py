""" Lists all videos contained inside YouTube playlist. """

from __future__ import annotations

import argparse
import os
import pickle
import pprint
import sys
import typing
from pathlib import Path

from google.auth.transport.requests import Request as APIRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource as GAPIResource
from googleapiclient.discovery import build as BuildResource
from googleapiclient.errors import HttpError

from ypl.__init__ import __version__

if typing.TYPE_CHECKING:
    from io import TextIO
    from typing import Callable, Generator, Iterator, Tuple

    from googleapiclient._apis.youtube.v3.resources import PlaylistItemsResource

_CLIENT_SECRETS_FILE = "client_secret.json"
_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
_API_SERVICE_NAME = "youtube"
_API_VERSION = "v3"


def config_path(name: str = __package__):
    base = Path.home()
    if os.name == "posix":
        if buf := os.getenv("XDG_CONFIG_HOME"):
            base = Path(buf) / name
        elif (hcfg := (base / ".config")).exists():
            base = hcfg / name
    elif os.name == "nt":
        if buf := os.getenv("APPDATA"):
            base = Path(buf) / name
    return base


def authenticate(headless: bool = True) -> GAPIResource:
    conf = config_path()
    cred = None
    stok = conf / ("." + __package__ + ".token")

    if stok.exists():
        with open(stok, "rb") as tok:
            cred = pickle.load(tok)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(APIRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                conf / _CLIENT_SECRETS_FILE, _SCOPES
            )
            cred = flow.run_console() if headless else flow.run_local_server(port=0)

        with open(stok, "wb") as tok:
            stok.chmod(0o600)
            pickle.dump(cred, tok)

    return BuildResource(_API_SERVICE_NAME, _API_VERSION, credentials=cred)


def enum_vids(
    id: str,
    page_size: int = 50,
    verbose: bool = False,
    printer: Callable[..., None] = pprint.PrettyPrinter(
        indent=4, stream=sys.stderr
    ).pprint,
) -> Generator[str, None, None]:
    api = authenticate(headless=False)
    if not api:
        # raise StopIteration
        return

    req = api.playlistItems().list(
        part="snippet",
        playlistId=id,
        maxResults=page_size,
        fields="items(id,snippet(title,resourceId/videoId)),nextPageToken",
    )

    obs = set()
    while req:
        tries = 2

        try:
            res = req.execute()
            if verbose:
                printer(res)

            for item in res["items"]:
                id = item["snippet"]["resourceId"]["videoId"]
                # avoid duplicates, just in case
                if id not in obs:
                    yield id
                    obs.add(id)
                elif verbose:
                    print("Duplicate filtered: {}".format(id), file=sys.stderr)

            req = api.playlistItems().list_next(req, res)

        except HttpError as err:
            # probably rate limiting, try again
            if err.resp.status in (403, 500, 503) and tries > 0:
                import time

                time.sleep(5)
                tries -= 1
            else:
                print(
                    "There was an error retrieving the playlist. Check the details:\n{}".format(
                        err._get_reason()
                    ),
                    file=sys.stderr,
                )
                raise


def print_iter(
    it: Iterator,
    fmt: str,
    sur: Tuple[str, str] = ("\n", "\n"),
    out: TextIO = sys.stderr,
):
    print(sur[0], file=out, end="")
    num = 0
    for n, v in enumerate(it):
        print(fmt.format(v))
        num = n + 1
    print(sur[1], file=out, end="")

    return num


def main():
    parser = argparse.ArgumentParser(
        description="{0} v{1} - {2}".format(__package__, __version__, __doc__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="{0} v{1}".format(__package__, __version__),
    )
    parser.add_argument("id", type=str, help="The playlist id.")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="increase output verbosity",
        action="store_true",
    )
    args = parser.parse_args()

    if not ((cfg := config_path()) / _CLIENT_SECRETS_FILE).exists():
        print(
            "Please ensure a {0} is located at {1}".format(_CLIENT_SECRETS_FILE, cfg),
            file=sys.stderr,
        )
        if not cfg.exists():
            cfg.mkdir(parents=False, exist_ok=True)

        sys.exit(1)

    num = print_iter(
        enum_vids(args.id, verbose=args.verbose),
        "https://www.youtube.com/watch?v={}",
        ("\n", "\n") if args.verbose else (str(), str()),
    )
    print("\nRetrieved {} elements.".format(num), file=sys.stderr)


if __name__ == "__main__":
    main()

# EOF
