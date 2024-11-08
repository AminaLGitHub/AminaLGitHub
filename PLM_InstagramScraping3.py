'''from datetime import datetime
import instaloader
import json
from typing import Dict
import csv
import pandas as pd

import json
import os
import re
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, IO, Iterator, List, Optional, Set, Union, cast
from urllib.parse import urlparse

import requests
import urllib3  # type: ignore

from .exceptions import *
from .instaloadercontext import InstaloaderContext, RateController
from .lateststamps import LatestStamps
from .nodeiterator import NodeIterator, resumable_iteration
from .sectioniterator import SectionIterator
from .structures import (Hashtag, Highlight, JsonExportable, Post, PostLocation, Profile, Story, StoryItem,
                         load_structure_from_file, save_structure_to_file, PostSidecarNode, TitlePic)

#Source: ChatGPT
#Prompt: save the following data to a csv file
def save_to_csv(data: dict, csv_file: str):
    """Save the parsed thread and replies to a CSV file"""
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=[
            "type", "text", "published_on", "id", "pk", "code", "username",
            "user_pic", "user_verified", "user_pk", "user_id", "has_audio",
            "reply_count", "like_count", "images", "image_count", "videos", "url"
        ])
        writer.writeheader()

        # Write the main post
        main_post = data["post"]
        main_post["type"] = "post"  # Add a type field to differentiate
        writer.writerow(main_post)

        # Write the replies
        for post in data["posts"]:
            post["type"] = "post"  # Mark as post
            writer.writerow(post)

#Source: https://instaloader.github.io/codesnippets.html#download-posts-in-a-specific-period
L = instaloader.Instaloader()
posts = instaloader.Hashtag.from_name(L.context, "saveGaza").get_posts()
SINCE = datetime(2023, 10, 7)  # further from today, inclusive
UNTIL = datetime(2024, 10, 8)  # closer to today, not inclusive

k = 0  # initiate k
#k_list = []  # uncomment this to tune k

for post in posts:
    postdate = post.date
    if postdate > UNTIL:
        continue
    elif postdate <= SINCE:
        k += 1
    else:
        L.download_post(post, "#saveGaza")
        # if you want to tune k, uncomment below to get your k max
        #k_list.append(k)
        k = 0  # set k to 0
        save_to_csv(posts, "saveGaza_Instagram_data.csv")
#max(k_list)

#lines 340-364 of https://github.com/instaloader/instaloader/blob/master/instaloader
def download_pic(self, filename: str, url: str, mtime: datetime,
                     filename_suffix: Optional[str] = None, _attempt: int = 1) -> bool:
        """Downloads and saves picture with given url under given directory with given timestamp.
        Returns true, if file was actually downloaded, i.e. updated."""
        if filename_suffix is not None:
            filename += '_' + filename_suffix
        urlmatch = re.search('\\.[a-z0-9]*\\?', url)
        file_extension = url[-3:] if urlmatch is None else urlmatch.group(0)[1:-1]
        nominal_filename = filename + '.' + file_extension
        if os.path.isfile(nominal_filename):
            self.context.log(nominal_filename + ' exists', end=' ', flush=True)
            return False
        resp = self.context.get_raw(url)
        if 'Content-Type' in resp.headers and resp.headers['Content-Type']:
            header_extension = '.' + resp.headers['Content-Type'].split(';')[0].split('/')[-1]
            header_extension = header_extension.lower().replace('jpeg', 'jpg')
            filename += header_extension
        else:
            filename = nominal_filename
        if filename != nominal_filename and os.path.isfile(filename):
            self.context.log(filename + ' exists', end=' ', flush=True)
            return False
        self.context.write_raw(resp, filename)
        os.utime(filename, (datetime.now().timestamp(), mtime.timestamp()))
        return True

#lines 366-376 of https://github.com/instaloader/instaloader/blob/master/instaloader
    def save_metadata_json(self, filename: str, structure: JsonExportable) -> None:
        """Saves metadata JSON file of a structure."""
        if self.compress_json:
            filename += '.json.xz'
        else:
            filename += '.json'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        save_structure_to_file(structure, filename)
        if isinstance(structure, (Post, StoryItem)):
            # log 'json ' message when saving Post or StoryItem
            self.context.log('json', end=' ', flush=True)

#lines 452-489 of https://github.com/instaloader/instaloader/blob/master/instaloader
def save_caption(self, filename: str, mtime: datetime, caption: str) -> None:
        """Updates picture caption / Post metadata info"""
        def _elliptify(caption):
            pcaption = caption.replace('\n', ' ').strip()
            return '[' + ((pcaption[:29] + "\u2026") if len(pcaption) > 31 else pcaption) + ']'
        filename += '.txt'
        caption += '\n'
        pcaption = _elliptify(caption)
        bcaption = caption.encode("UTF-8")
        with suppress(FileNotFoundError):
            with open(filename, 'rb') as file:
                file_caption = file.read()
            if file_caption.replace(b'\r\n', b'\n') == bcaption.replace(b'\r\n', b'\n'):
                try:
                    self.context.log(pcaption + ' unchanged', end=' ', flush=True)
                except UnicodeEncodeError:
                    self.context.log('txt unchanged', end=' ', flush=True)
                return None
            else:
                def get_filename(index):
                    return filename if index == 0 else '{0}_old_{2:02}{1}'.format(*os.path.splitext(filename), index)

                i = 0
                while os.path.isfile(get_filename(i)):
                    i = i + 1
                for index in range(i, 0, -1):
                    os.rename(get_filename(index - 1), get_filename(index))
                try:
                    self.context.log(_elliptify(file_caption.decode("UTF-8")) + ' updated', end=' ', flush=True)
                except UnicodeEncodeError:
                    self.context.log('txt updated', end=' ', flush=True)
        try:
            self.context.log(pcaption, end=' ', flush=True)
        except UnicodeEncodeError:
            self.context.log('txt', end=' ', flush=True)
        with open(filename, 'w', encoding='UTF-8') as fio:
            fio.write(caption)
        os.utime(filename, (datetime.now().timestamp(), mtime.timestamp()))'''

#Source 1: https://instaloader.github.io/codesnippets.html#download-posts-in-a-specific-period
#Source 2: parse through instagram posts using instaloader and add the url of the post to a column, the path of the image to an additional column, the caption of the post to a column, save the information to a json file; what other information can be obtained from the post?; convert a json file to a csv file

import instaloader
import os
import json
import csv
import time
from datetime import datetime

# Initialize Instaloader
L = instaloader.Instaloader()

'''# Login to Instagram
username = input("Enter your Instagram username: ")
# Load previously saved session if available
try:
    L.load_session_from_file(username)
    print(f"Successfully loaded session for {username}.")
except FileNotFoundError:
    print("No session found, logging in.")
    password = input("Enter your Instagram password: ")
    try:
        # Standard login
        L.login(username, password)
        L.save_session_to_file()  # Save session for future use
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        # Handle two-factor authentication (2FA)
        two_factor_code = input("Enter the two-factor authentication code sent to your device: ")
        L.two_factor_login(two_factor_code)
        L.save_session_to_file()  # Save session after 2FA login'''

# Define the hashtag and date range
# Once CSV is downloaded for hashtag, replace hashtag and repeat with rest of hashtags
# Replace hashtags in lines 190 and 207, and rename file names according to hashtags in lines 236 and 240
posts = instaloader.Hashtag.from_name(L.context, "saveGaza").get_posts()
SINCE = datetime(2023, 10, 7)  # Start date, inclusive
UNTIL = datetime(2024, 10, 8)  # End date, not inclusive

# List to store post data
post_data = []

# Iterate through posts
for post in posts:
    time.sleep(2) # Wait for 2 seconds between requests
    postdate = post.date
    if postdate > UNTIL:
        continue
    elif postdate <= SINCE:
        break  # Stop if the post is older than the start date
    else:
        # Download the post image
        L.download_post(post, "#saveGaza")

        # Extract the post data
        post_info = {
            "pic_url": post.url,  # Pic URL
            "date_posted": post.date,  # Datetime object
            "post_type": post.typename, #Post Type
            "caption": post.caption,  # Post caption
            "likes_number": post.likes, #Number of Likes
            "comments_number": post.comments, # Number of Comments
            "hashtags": post.caption_hashtags,  # List of hashtags
            "is_video": post.is_video, #Is post a video?
            "video_url": post.video_url if post.is_video else None, #Video URL
            "view_number": post.video_view_count if post.is_video else None, #Number of Views (for video)
            "is_sponsored": post.is_sponsored, #Is the post sponsored?
            "post_path": os.path.join(L.dirname_pattern, L.filename_pattern.format(post=post)),  # Post file path
        }

        # Append the post info to the list
        post_data.append(post_info)

# Save the post data to a JSON file
output_file = "saveGaza_instagram_data.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(post_data, f, ensure_ascii=False, indent=4)

print(f"Data saved to {output_file}")

# Load JSON data from a file
with open('saveGaza_instagram_data_extended.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Open a CSV file to write the data
with open('saveGaza_instagram_data_extended.csv', 'w', newline='', encoding='utf-8') as csv_file:
    # Create a CSV writer object
    csv_writer = csv.writer(csv_file)

    # Write the header (column names)
    header = data[0].keys()  # Assuming all dicts have the same keys
    csv_writer.writerow(header)

    # Write the rows (data)
    for post in data:
        csv_writer.writerow(post.values())

print("JSON data successfully converted to CSV.")

#Uncomment when all CSV files are created
'''# Merge CSV files into one CSV file
    df_1 = pd.read_csv('saveGaza_Instagram_data.csv')
    df_2 = pd.read_csv('PalestineLivesMatter_Instagram_data.csv')
    df_3 = pd.read_csv('Palestine_Instagram_data.csv')
    df_4 = pd.read_csv('Gaza_Instagram_data.csv')
    df_5 = pd.read_csv('saveRafah_Instagram_data.csv')
    df_6 = pd.read_csv('saveKhanYounis_Instagram_data.csv')
    merged_df = pd.concat([df_1, df_2, df_3, df_4, df_5, df_6], ignore_index=True)
    merged_df.to_csv('ALL_PLM_Instagram_Posts.csv', index=False)'''