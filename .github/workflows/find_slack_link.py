import sys
import os
import argparse

try: 
	from urlparse import urljoin # Python2
except ImportError: 
	from urllib.parse import urljoin # Python3

import autoscraper

info_lookup = {
	"win32": [
		"https://slack.com/downloads/windows", 
		"https://slack.com/downloads/instructions/windows", 
		"exe"
	],
	"linux": [
		"https://slack.com/downloads/linux",
		"https://slack.com/downloads/instructions/fedora",
		"rpm"
	],
	"darwin": [
		"https://slack.com/downloads/mac",
		"https://slack.com/downloads/instructions/mac",
		"dmg"
	]
}

platform = sys.platform
if platform.startswith("linux"):
	platform = "linux"

(download_landing_page_link, 
 os_instruction_link, download_file_ext) = info_lookup[platform]

model_dir = os.path.dirname(os.path.abspath(__file__))
scraper = autoscraper.AutoScraper()

scraper.load(os.path.join(model_dir, "slack_version.json"))
version_text = scraper.get_result_exact(download_landing_page_link)[0]
version = version_text[len('Version '):]

scraper.load(os.path.join(model_dir, "slack_download_url.json"))
download_url = scraper.get_result_exact(os_instruction_link)[0]
download_url = urljoin(os_instruction_link, download_url)

print("::set-env name=SLACK_VERSION::{}".format(verson))
print("::set-env name=SLACK_DOWNLOAD_URL::{}".format(download_url))
