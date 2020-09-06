import sys
import os
import io

try: 
	from urlparse import urljoin # Python2
except ImportError: 
	from urllib.parse import urljoin # Python3

import requests
import htmlement

if sys.platform == "win32":
	download_landing_page_link = "https://slack.com/downloads/windows"
	os_instruction_link = "https://slack.com/downloads/instructions/windows"
elif sys.platform.startswith("linux"):
	download_landing_page_link = "https://slack.com/downloads/linux"
	os_instruction_link = "https://slack.com/downloads/instructions/fedora"
elif sys.platform == "darwin":
	download_landing_page_link = "https://slack.com/downloads/mac"
	os_instruction_link = "https://slack.com/downloads/instructions/mac"
else:
	raise ValueError("invalid platform")

html_page = requests.get(os_instruction_link)
html = html_page.content.decode("utf-8")
tree = htmlement.fromstring(html)
download_link = next(iter((item for item in tree.iterfind(".//a") if item.text == 'Try again'))).get('href')
download_link = urljoin(os_instruction_link, download_link)
print("::set-env name=SLACK_DOWNLOAD_URL::{}".format(download_link))

html_page = requests.get(download_landing_page_link)
html = html_page.content.decode("utf-8")
tree = htmlement.fromstring(html)
version_text = next(iter((item for item in tree.iterfind(".//strong") if item.text.startswith('Version ')))).text
verson = version_text[len('Version '):]
print("::set-env name=SLACK_VERSION::{}".format(verson))

