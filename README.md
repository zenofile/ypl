# ypl

Extract video URLs from YouTube's playlists using the Google API.

------------------------------------

## Prelude

A `client_secret.json` is expected at `${XDG_CONFIG_HOME}/ypl/` (Linux) or `%APPDATA%/ypl/` (Windows). To generate one, please visit the
[YouTube Data API](https://developers.google.com/youtube/v3/quickstart/python#step_1_set_up_your_project_and_credentials) quickstart guide.

## Install

    python3 -m pip install --user git+https://github.com/zenofile/ypl.git
