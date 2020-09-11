import os
import argparse

from urllib.parse import urljoin

import autoscraper

parser = argparse.ArgumentParser()
parser.add_argument("platform")
parser.add_argument('--get-version', action="store_true")
parser.add_argument('--get-download-url', action="store_true")
args = parser.parse_args()

info_lookup = {
	"windows": [
		"https://slack.com/downloads/windows", 
		"https://slack.com/downloads/instructions/windows", 
		"exe"
	],
	"ubuntu": [
		"https://slack.com/downloads/linux",
		"https://slack.com/downloads/instructions/fedora",
		"rpm"
	],
	"macOS": [
		"https://slack.com/downloads/mac",
		"https://slack.com/downloads/instructions/mac",
		"dmg"
	]
}

(download_landing_page_link, 
 os_instruction_link, download_file_ext) = info_lookup[args.platform]

model_dir = os.path.dirname(os.path.abspath(__file__))
scraper = autoscraper.AutoScraper()

if args.get_version:
	scraper.load(os.path.join(model_dir, "slack_version.json"))
	version_text = scraper.get_result_exact(download_landing_page_link)[0]
	version = version_text[len('Version '):]
	print(version)

if args.get_download_url:
	scraper.load(os.path.join(model_dir, "slack_download_url.json"))
	download_url = scraper.get_result_exact(os_instruction_link)[0]
	download_url = urljoin(os_instruction_link, download_url)
	print(download_url)
