"""
Instagram Graph API — post images automatically.

Requirements:
- Instagram Business or Creator account
- Access token with instagram_content_publish permission
- Instagram User ID (numeric)

Token expires every 60 days — see SETUP.md for how to refresh.
"""

import os
import time
import requests

GRAPH = "https://graph.facebook.com/v19.0"


def post_image(image_url: str, caption: str, user_id: str, access_token: str) -> dict:
    """
    Post an image to Instagram.
    Returns {"id": "instagram_post_id"}.
    """

    # Step 1 — create media container
    r = requests.post(
        f"{GRAPH}/{user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    _check(r, "creating media container")
    container_id = r.json()["id"]

    # Instagram needs a moment to process the image
    time.sleep(4)

    # Step 2 — publish
    r = requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    _check(r, "publishing media")
    return r.json()


def post_carousel(image_urls: list, caption: str, user_id: str, access_token: str) -> dict:
    """
    Post a carousel to Instagram (up to 10 slides).
    image_urls: list of public HTTPS image URLs, one per slide.
    Returns {"id": "instagram_post_id"}.
    """

    # Step 1 — create a media container for each slide
    container_ids = []
    for i, url in enumerate(image_urls, 1):
        r = requests.post(
            f"{GRAPH}/{user_id}/media",
            data={
                "image_url": url,
                "is_carousel_item": "true",
                "access_token": access_token,
            },
            timeout=30,
        )
        _check(r, f"creating container for slide {i}")
        container_ids.append(r.json()["id"])

    # Give Instagram a moment to process
    time.sleep(5)

    # Step 2 — create the carousel container
    r = requests.post(
        f"{GRAPH}/{user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(container_ids),
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    _check(r, "creating carousel container")
    carousel_id = r.json()["id"]

    time.sleep(5)

    # Step 3 — publish
    r = requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={
            "creation_id": carousel_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    _check(r, "publishing carousel")
    return r.json()


def verify_credentials(user_id: str, access_token: str) -> str:
    """Check credentials and return Instagram username, or raise on failure."""
    r = requests.get(
        f"{GRAPH}/{user_id}",
        params={"fields": "username,name", "access_token": access_token},
        timeout=10,
    )
    _check(r, "verifying credentials")
    data = r.json()
    return data.get("username", user_id)


def refresh_token(access_token: str, app_id: str, app_secret: str) -> str:
    """
    Extend a long-lived token for another 60 days.
    Call this in your GitHub Action monthly to avoid expiry.
    Returns new token string.
    """
    r = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": access_token,
        },
        timeout=15,
    )
    _check(r, "refreshing token")
    return r.json()["access_token"]


def _check(response: requests.Response, action: str):
    """Raise a clear error if the API call failed."""
    if response.status_code != 200:
        try:
            err = response.json().get("error", {})
            msg = err.get("message", response.text[:200])
            code = err.get("code", response.status_code)
        except Exception:
            msg = response.text[:200]
            code = response.status_code
        raise RuntimeError(f"Instagram API error while {action} (code {code}): {msg}")
