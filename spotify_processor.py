import os
from typing import Dict, List, Optional, Tuple

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SPOTIFY_SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"


def _get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    env_value = os.getenv(key)
    if env_value:
        return env_value

    try:
        import streamlit as st

        secret_value = st.secrets.get(key)
        if secret_value:
            return str(secret_value)
    except Exception:
        pass

    return default


def spotify_is_configured() -> bool:
    return bool(_get_setting("SPOTIPY_CLIENT_ID") and _get_setting("SPOTIPY_CLIENT_SECRET"))


def build_auth_manager(cache_path: str) -> SpotifyOAuth:
    redirect_uri = _get_setting("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8501")
    return SpotifyOAuth(
        client_id=_get_setting("SPOTIPY_CLIENT_ID"),
        client_secret=_get_setting("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPES,
        cache_path=cache_path,
        show_dialog=False,
        open_browser=False,
    )


def get_spotify_client(auth_manager: SpotifyOAuth, auth_code: Optional[str] = None) -> Tuple[Optional[spotipy.Spotify], Optional[str]]:
    token_info = auth_manager.get_cached_token()

    if not token_info and auth_code:
        try:
            token_info = auth_manager.get_access_token(auth_code, check_cache=False)
        except Exception as exc:
            return None, f"Spotify login failed: {exc}"

    if not token_info:
        return None, "Spotify is not connected yet."

    if auth_manager.is_token_expired(token_info):
        try:
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
        except Exception as exc:
            return None, f"Spotify token refresh failed: {exc}"

    return spotipy.Spotify(auth=token_info["access_token"]), None


def get_available_devices(sp: spotipy.Spotify) -> List[Dict]:
    try:
        devices = sp.devices().get("devices", [])
        return devices
    except Exception:
        return []


def play_track_by_query(sp: spotipy.Spotify, query: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
    try:
        results = sp.search(q=query, type="track", limit=1)
        tracks = results.get("tracks", {}).get("items", [])
        if not tracks:
            return False, "No matching track found."

        track = tracks[0]
        track_uri = track["uri"]
        track_name = track["name"]
        artist_name = track["artists"][0]["name"] if track.get("artists") else "Unknown"

        sp.start_playback(device_id=device_id, uris=[track_uri])
        return True, f"Now playing: {track_name} - {artist_name}"
    except Exception as exc:
        return False, f"Could not start playback: {exc}"


def pause_playback(sp: spotipy.Spotify, device_id: Optional[str] = None) -> Tuple[bool, str]:
    try:
        sp.pause_playback(device_id=device_id)
        return True, "Playback paused."
    except Exception as exc:
        return False, f"Could not pause playback: {exc}"


def resume_playback(sp: spotipy.Spotify, device_id: Optional[str] = None) -> Tuple[bool, str]:
    try:
        sp.start_playback(device_id=device_id)
        return True, "Playback resumed."
    except Exception as exc:
        return False, f"Could not resume playback: {exc}"


def next_track(sp: spotipy.Spotify, device_id: Optional[str] = None) -> Tuple[bool, str]:
    try:
        sp.next_track(device_id=device_id)
        return True, "Skipped to next track."
    except Exception as exc:
        return False, f"Could not skip to next track: {exc}"


def previous_track(sp: spotipy.Spotify, device_id: Optional[str] = None) -> Tuple[bool, str]:
    try:
        sp.previous_track(device_id=device_id)
        return True, "Went back to previous track."
    except Exception as exc:
        return False, f"Could not go to previous track: {exc}"
