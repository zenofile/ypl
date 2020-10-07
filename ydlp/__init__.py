#!/usr/bin/env python3

from __future__ import annotations

import argparse
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

if typing.TYPE_CHECKING:
    from io import TextIO
    from typing import Callable, Generator, Iterator, Tuple

    from googleapiclient._apis.youtube.v3.resources import PlaylistItemsResource

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def config_path():
    # ignore XDG spec for now
    base = home = Path.home()
    # if os.name == "posix":
    if (home / ".config").exists():
        try:
            base = base / ".config/ydlp"
            base.mkdir(parents=False, exist_ok=True)
        except FileNotFoundError:
            base = home
    return base


def authenticate(headless: bool = True) -> GAPIResource:
    conf = config_path()
    cred = None
    stok = conf / ".ydlp.token"

    if stok.exists():
        with open(stok, "rb") as tok:
            cred = pickle.load(tok)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(APIRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                conf / CLIENT_SECRETS_FILE, SCOPES
            )
            cred = flow.run_console() if headless else flow.run_local_server(port=0)

        with open(stok, "wb") as tok:
            stok.chmod(0o600)
            pickle.dump(cred, tok)

    return BuildResource(API_SERVICE_NAME, API_VERSION, credentials=cred)


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
        prog="ydlp", description="Lists all videos inside a playlist."
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

    num = print_iter(
        enum_vids(args.id, verbose=args.verbose),
        "https://www.youtube.com/watch?v={}",
        ("\n", "\n") if args.verbose else (str(), str()),
    )
    print("\nRetrieved {} elements.".format(num), file=sys.stderr)


if __name__ == "__main__":
    main()

# EOF
