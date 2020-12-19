import os
import argparse
import re

import urllib
from urllib.parse import urljoin, urlparse

import autoscraper

parser = argparse.ArgumentParser()
parser.add_argument("platform")
parser.add_argument('--get-version', action="store_true")
parser.add_argument('--get-download-url', action="store_true")
args = parser.parse_args()


def get_url(platform):
	lookup = {
		"windows": "https://slack.com/ssb/download-win64-msi",
		"macOS": "https://slack.com/ssb/download-osx",
	}
	if platform in lookup:
		return urllib.request.urlopen(lookup[platform]).geturl()
	# Handle Ubuntu
	scraper = autoscraper.AutoScraper()
	return scraper.build("https://slack.com/downloads/instructions/fedora", 
		[re.compile(r"https://downloads\.slack-edge\.com/linux_releases/slack-.*")])[0]


def get_version(platform):
	url = get_url(platform)
	parts = urlparse(url).path.split("/")
	if platform in ["windows", "macOS"]:
		return parts[3]
	g = re.match(r'slack-((\d+\.)+\d+)-', parts[-1])
	return g.group(1)


model_dir = os.path.dirname(os.path.abspath(__file__))
scraper = autoscraper.AutoScraper()

if args.get_download_url:
	url = get_url(args.platform)
	print(url)

if args.get_version:
	version = get_version(args.platform)
	print(version)