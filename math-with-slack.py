#!/usr/bin/env python

################################################################################
# Rendered math (MathJax) with Slack's desktop client
################################################################################
#
# Slack (https://slack.com) does not display rendered math. This script
# injects MathJax (https://www.mathjax.org) into Slack's desktop client,
# which allows you to write nice-looking inline- and display-style math
# using familiar TeX/LaTeX syntax.
#
# https://github.com/fsavje/math-with-slack
#
# MIT License, Copyright 2017-2019 Fredrik Savje
#
################################################################################

# Python 2.7

from __future__ import print_function


# Load modules

import argparse
import json
import os
import shutil
import struct
import sys


# Math with Slack version

mws_version = '0.3.0.9000'


# Parse command line options

parser = argparse.ArgumentParser(prog='math-with-slack', description='Inject Slack with MathJax.')
parser.add_argument('-a', '--app-file', help='Path to Slack\'s \'app.asar\' file.')
parser.add_argument('-s', '--settings-file', help='Path to Slack\'s \'local-settings.json\' file.')
parser.add_argument('-u', '--uninstall', action='store_true', help='Removes injected MathJax code.')
parser.add_argument('--version', action='version', version='%(prog)s ' + mws_version)
args = parser.parse_args()


# Misc functions

def exprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)


# Find path to app.asar

if args.app_file is not None:
    app_path = args.app_file
elif sys.platform == 'darwin':
    app_path = '/Applications/Slack.app/Contents/Resources/app.asar'
elif sys.platform == 'linux':
    for test_app_file in [
        '/usr/lib/slack/resources/app.asar',
        '/usr/local/lib/slack/resources/app.asar',
        '/opt/slack/resources/app.asar'
    ]:
        if os.path.isfile(test_app_file):
            app_path = test_app_file
            break
elif sys.platform == 'win32':
    import glob
    app_path = glob.glob(
        os.path.join(os.environ["UserProfile"],
                     "AppData\\Local\\slack\\app-?.*.*/resources/app.asar"))[-1]
    


# Check so app.asar file exists

try:
    if not os.path.isfile(app_path):
        exprint('Cannot find Slack at: ' + app_path)
except NameError:
    exprint('Could not find Slack\'s app.asar file. Please provide path.')


# Find path to local-settings.json

if args.settings_file is not None:
    settings_path = args.settings_file
elif sys.platform == 'darwin':
    for test_settings_file in [
        os.path.expandvars('${HOME}/Library/Application Support/Slack/local-settings.json'),
        os.path.expandvars('${HOME}/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack/local-settings.json')
    ]:
        if os.path.isfile(test_settings_file):
            settings_path = test_settings_file
            break
elif sys.platform == 'linux':
    exprint('Not implemented')
elif sys.platform == 'win32':
    settings_path = os.path.expandvars('%AppData%\\Slack\\local-settings.json')


# Check so local-settings.json file exists

try:
    if not os.path.isfile(settings_path):
        exprint('Cannot find settings file at: ' + settings_path)
except NameError:
    exprint('Could not find local-settings.json. Please provide path.')


# Print info

print('Using Slack installation at: ' + app_path)
print('Using local settings file at: ' + settings_path)


# Update local settings file

with open(settings_path, mode='r') as settings_file:
    settings_json = json.load(settings_file)

if args.uninstall:
    if 'bootSonic.mwsbak' in settings_json:
        settings_json['bootSonic'] = settings_json['bootSonic.mwsbak']
        del settings_json['bootSonic.mwsbak']
else:
    if 'bootSonic.mwsbak' not in settings_json:
        settings_json['bootSonic.mwsbak'] = settings_json['bootSonic']
    settings_json['bootSonic'] = 'never'

try:
    with open(settings_path, mode='w') as settings_file:
        json.dump(settings_json, settings_file, separators=(',', ':'))
except Exception as e:
    print(e)
    exprint('Cannot update settings file. Make sure the script has write permissions.')


# Remove previously injected code if it exists

with open(app_path, mode='rb') as check_app_fp:
    (header_data_size, json_binary_size) = struct.unpack('<II', check_app_fp.read(8))
    assert header_data_size == 4
    json_binary = check_app_fp.read(json_binary_size)

(json_data_size, json_string_size) = struct.unpack('<II', json_binary[:8])
assert json_binary_size == json_data_size + 4
json_check = json.loads(json_binary[8:(json_string_size + 8)].decode('utf-8'))

if 'MWSINJECT' in json_check['files']:
    if not os.path.isfile(app_path + '.mwsbak'):
        exprint('Found injected code without backup. Please re-install Slack.')
    try:
        os.remove(app_path)
        shutil.move(app_path + '.mwsbak', app_path)
    except Exception as e:
        print(e)
        exprint('Cannot remove previously injected code. Make sure the script has write permissions.')


# Remove old backup if it exists

if os.path.isfile(app_path + '.mwsbak'):
    try:
        os.remove(app_path + '.mwsbak')
    except Exception as e:
        print(e)
        exprint('Cannot remove old backup. Make sure the script has write permissions.')


# Are we uninstalling?

if args.uninstall:
    print('Uninstall successful. Please restart Slack.')
    sys.exit(0)


### Inject code

# Code to be injected

inject_code = ('\n\n// math-with-slack ' + mws_version + '''
// https://github.com/fsavje/math-with-slack
document.addEventListener('DOMContentLoaded', function() {
  var mathjax_config = document.createElement('script');
  mathjax_config.type = 'text/x-mathjax-config';
  mathjax_config.text = `
    MathJax.Hub.Config({
      messageStyle: 'none',
      extensions: ['tex2jax.js'],
      jax: ['input/TeX', 'output/HTML-CSS'],
      tex2jax: {
        displayMath: [['$$', '$$']],
        element: 'msgs_div',
        ignoreClass: 'ql-editor',
        inlineMath: [['$', '$']],
        processEscapes: true,
        skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      },
      TeX: {
        extensions: ['AMSmath.js', 'AMSsymbols.js', 'noErrors.js', 'noUndefined.js']
      }
    });
  `;

  var mathjax_observer = document.createElement('script');
  mathjax_observer.type = 'text/x-mathjax-config';
  mathjax_observer.text = `
    var target = document.querySelector('#messages_container');
    var options = { attributes: false, childList: true, characterData: true, subtree: true };
    var observer = new MutationObserver(function (r, o) { MathJax.Hub.Queue(['Typeset', MathJax.Hub]); });
    observer.observe(target, options);
  `;

  var mathjax_script = document.createElement('script');
  mathjax_script.type = 'text/javascript';
  mathjax_script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js';

  document.head.appendChild(mathjax_config);
  document.head.appendChild(mathjax_observer);
  document.head.appendChild(mathjax_script);
});
''').encode('utf-8')


# Make backup

try:
    shutil.move(app_path, app_path + '.mwsbak')
except Exception as e:
    print(e)
    exprint('Cannot make backup. Make sure the script has write permissions.')


# Get file info

with open(app_path + '.mwsbak', mode='rb') as ori_app_fp:
    (header_data_size, json_binary_size) = struct.unpack('<II', ori_app_fp.read(8))
    assert header_data_size == 4
    json_binary = ori_app_fp.read(json_binary_size)
    ori_data_offset = 8 + json_binary_size
    ori_app_fp.seek(0, 2)
    ori_data_size = ori_app_fp.tell() - ori_data_offset

(json_data_size, json_string_size) = struct.unpack('<II', json_binary[:8])
assert json_binary_size == json_data_size + 4
json_header = json.loads(json_binary[8:(json_string_size + 8)].decode('utf-8'))
assert 'MWSINJECT' not in json_header['files']
ori_ssbinterop_size = json_header['files']['dist']['files']['ssb-interop.bundle.js']['size']
ori_ssbinterop_offset = int(json_header['files']['dist']['files']['ssb-interop.bundle.js']['offset'])


# Modify JSON data

json_header['files']['MWSINJECT'] = json_header['files']['LICENSE']
json_header['files']['dist']['files']['ssb-interop.bundle.js']['size'] = ori_ssbinterop_size + len(inject_code)
json_header['files']['dist']['files']['ssb-interop.bundle.js']['offset'] = str(ori_data_size)


# Write new app.asar file

new_json_header = json.dumps(json_header, separators=(',', ':')).encode('utf-8')
new_json_header_padding = (4 - len(new_json_header) % 4) % 4

with open(app_path + '.mwsbak', mode='rb') as ori_app_fp, \
     open(app_path, mode='wb') as new_app_fp:
    # Header
    new_app_fp.write(struct.pack('<I', 4))
    new_app_fp.write(struct.pack('<I', 8 + len(new_json_header) + new_json_header_padding))
    new_app_fp.write(struct.pack('<I', 4 + len(new_json_header) + new_json_header_padding))
    new_app_fp.write(struct.pack('<I', len(new_json_header)))
    new_app_fp.write(new_json_header)
    new_app_fp.write(b'\0' * new_json_header_padding)
    # Old data
    ori_app_fp.seek(ori_data_offset)
    shutil.copyfileobj(ori_app_fp, new_app_fp)
    # Modified ssb-interop.bundle.js
    ori_app_fp.seek(ori_data_offset + ori_ssbinterop_offset)
    copy_until = ori_app_fp.tell() + ori_ssbinterop_size
    while ori_app_fp.tell() < copy_until:
        new_app_fp.write(ori_app_fp.read(min(65536, copy_until - ori_app_fp.tell())))
    new_app_fp.write(inject_code)


# We are done

print('Install successful. Please restart Slack.')
sys.exit(0)


# References

# https://github.com/electron/node-chromium-pickle-js
# https://chromium.googlesource.com/chromium/src/+/master/base/pickle.h
# https://github.com/electron/asar
# https://github.com/electron-archive/node-chromium-pickle
# https://github.com/leovoel/BeautifulDiscord/tree/master/beautifuldiscord
