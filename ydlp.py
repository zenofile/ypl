import os
import stat
import sys
import pickle
import argparse
import pprint
import google.oauth2.credentials

from contextlib import suppress
from typing import Iterator, Set, List, Tuple, Callable

from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


def authenticate(headless: bool = True) -> Resource:
    creds = None
    if os.path.exists('.token'):
        with open('.token', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            if not headless:
                credentials = flow.run_local_server()
            else:
                credentials = flow.run_console()
            creds = flow.run_local_server(port=0)
        with open('.token', 'wb') as token:
            with suppress(OSError):
                os.fchmod(token.fileno(), stat.S_IRUSR | stat.S_IWUSR)
            pickle.dump(creds, token)
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)


def enum_vids(
    id: str,
    page_size: int = 50,
    verbose: bool = False,
    printer: Callable[..., None] = pprint.PrettyPrinter(indent=4).pprint
) -> List[Iterator]:
    api = authenticate(headless=False)
    if api:
        request = api.playlistItems().list(part="snippet",
                                           playlistId=id,
                                           maxResults=page_size)
        while request:
            response = request.execute()
            if verbose:
                printer(response)
            
            yield map(lambda l: l['snippet']['resourceId']['videoId'],
                      response['items'])
            request = api.playlistItems().list_next(request, response)


def main():
    parser = argparse.ArgumentParser(
        prog='ydlp', description='Lists all videos inside a playlist.')
    parser.add_argument('id', type=str, help='The playlist id.')
    parser.add_argument('-v',
                        '--verbose',
                        dest='verbose',
                        help='increase output verbosity',
                        action='store_true')
    args = parser.parse_args()
    # build set from list of map iterators and prepend URI prefix
    if args.verbose:
        print('\n' * 2, file=sys.stderr)
    vids = {e for m in enum_vids(args.id, verbose=args.verbose) for e in m}
    if args.verbose:
        print('\n' * 2, file=sys.stderr)
    for vid in vids:
        print('https://www.youtube.com/watch?v={}'.format(vid))
    print('\nExtracted {} elements.'.format(len(vids)), file=sys.stderr)


if __name__ == "__main__":
    main()

#EOF
