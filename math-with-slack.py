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

# Python 2.7 and 3

from __future__ import print_function


# Load modules

import argparse
import json
import os
import shutil
import struct
import sys

try:
    # Python 3
    import urllib.request as urllib_request
except:
    # Python 2
    import urllib as urllib_request

import tarfile
import tempfile


# Math with Slack version

mws_version = '0.3.0.9000'


# Parse command line options

parser = argparse.ArgumentParser(prog='math-with-slack', description='Inject Slack with MathJax.')
parser.add_argument('-a', '--app-file', help='Path to Slack\'s \'app.asar\' file.')
parser.add_argument('--mathjax-url', 
                    help='Url to download mathjax release.', 
                    default='https://registry.npmjs.org/mathjax/-/mathjax-3.0.0.tgz')
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
elif sys.platform.startswith('linux'):
    for test_app_file in [
        '/usr/lib/slack/resources/app.asar',
        '/usr/local/lib/slack/resources/app.asar',
        '/opt/slack/resources/app.asar'
    ]:
        if os.path.isfile(test_app_file):
            app_path = test_app_file
            break
elif sys.platform == 'win32':
   exprint('Not implemented')


# Check so app.asar file exists

try:
    if not os.path.isfile(app_path):
        exprint('Cannot find Slack at: ' + app_path)
except NameError:
    exprint('Could not find Slack\'s app.asar file. Please provide path.')



# Print info

print('Using Slack installation at: ' + app_path)


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
// Inject MathJax 3.
// Credit to initial implementation: https://github.com/fsavje/math-with-slack
document.addEventListener('DOMContentLoaded', function() {

  function typeset(element) {
    const MathJax = window.MathJax;
    MathJax.startup.promise = MathJax.startup.promise
      .then(() => {return MathJax.typesetPromise(element);})
      .catch((err) => console.log('Typeset failed: ' + err.message));
    return MathJax.startup.promise;
  }

  window.MathJax = {
    loader: {load: ['[tex]/ams', '[tex]/color', '[tex]/noerrors', '[tex]/noundefined', '[tex]/boldsymbol']},
    tex: {
      packages: {'[+]': ['ams', 'color', 'noerrors', 'noundefined', 'boldsymbol']},
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']],
      // the following doesn't seem to work with MathJax 3
      // skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    },
    startup: {
      ready: () => {
        MathJax = window.MathJax;
        MathJax.startup.defaultReady();
        var entry_observer = new IntersectionObserver(
          (entries, observer) => {
            var appearedEntries = entries.filter((entry) => entry.intersectionRatio > 0);
            console.log(appearedEntries);
            typeset(appearedEntries.map((entry) => entry.target));
          }, 
          { root: document.body }
        );
        var target = document.body.addEventListener("DOMNodeInserted", 
            function(event) {
                var target = event.relatedNode;
                if(target && typeof target.getElementsByClassName === 'function') {
                    // span.c-message_kit__text for messages in the Threads View
                    // span.c-message__body for messages in the chats (i.e. direct messages)
                    var messages = target.querySelectorAll('span.c-message__body, span.c-message_kit__text, div.p-rich_text_block');
                    for (var i = 0; i < messages.length; i++) {
                        msg = messages[i];
                        entry_observer.observe(msg);
                    }
                }
            }
        );
      }
    },
  };

  // Import mathjax
  require("mathjax/es5/tex-svg-full");

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


injected_file_name = 'main-preload-entry-point.bundle.js'
ori_injected_file_size = json_header['files']['dist']['files'][injected_file_name]['size']
ori_injected_file_offset = int(json_header['files']['dist']['files'][injected_file_name]['offset'])


# Modify JSON data

json_header['files']['MWSINJECT'] = json_header['files']['LICENSE']
json_header['files']['dist']['files'][injected_file_name]['size'] = ori_injected_file_size + len(inject_code)
json_header['files']['dist']['files'][injected_file_name]['offset'] = str(ori_data_size)

def split_path_to_components(path):
    dirs = []
    while True:
        path, dir = os.path.split(path)
        if dir != "":
            dirs.append(dir)
        else:
            if path != "":
                dirs.append(dir)
            break
    dirs.reverse()
    if dirs == ['.']:
        return dirs
    else:
        return ['.'] + dirs

def dir_to_json_header(root_dir, initial_offset):
    """Returns the json header for `root_dir`.
    
    Args:
        - root_dir: the root_dir 
        - initial_offset: a number that is added to all offset of files

    Returns:
        a tuple of (result, file_paths), where result is a dict containing
        the json header, and file_paths is a list of file paths in order 
        that should be appended to the end of the .asar file. 
    """
    file_paths = []
    result = {"files": {}}
    offset = initial_offset
    for parent_abs, dirs, files in os.walk(root_dir):
        parent = os.path.relpath(parent_abs, root_dir)
        parent_components = split_path_to_components(parent)
        rdict = result
        for dir_component in parent_components[:-1]:
            rdict = rdict["files"][dir_component]
        rdict["files"][parent_components[-1]] = {"files": {}}
        for file in files:
            file_path = os.path.join(parent_abs, file)
            file_paths.append(file_path)
            size = os.path.getsize(file_path)
            rdict["files"][parent_components[-1]]["files"][file] = {'size': size, 'offset': str(offset)}
            offset += size
    return result, file_paths

# Download MathJax, currently assumes downloaded file is a tar called package.tar

mathjax_tar_name, headers = urllib_request.urlretrieve(args.mathjax_url)
mathjax_tmp_dir = tempfile.mkdtemp()
mathjax_tar = tarfile.open(mathjax_tar_name)
mathjax_tar.extractall(path=mathjax_tmp_dir)
mathjax_tar.close()
mathjax_dir = os.path.join(mathjax_tmp_dir, "package")
mathjax_json_header, append_file_paths = dir_to_json_header(mathjax_dir, ori_data_size + ori_injected_file_size + len(inject_code))
json_header["files"]["node_modules"]["files"]["mathjax"] = mathjax_json_header["files"]["."]


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
    # Modified injected_file
    ori_app_fp.seek(ori_data_offset + ori_injected_file_offset)
    copy_until = ori_app_fp.tell() + ori_injected_file_size
    while ori_app_fp.tell() < copy_until:
        new_app_fp.write(ori_app_fp.read(min(65536, copy_until - ori_app_fp.tell())))
    new_app_fp.write(inject_code)
    # Append MathJax files in sequence
    new_app_fp.seek(0, 2)
    for append_file_path in append_file_paths:
        with open(append_file_path, 'rb') as append_file:
            new_app_fp.write(append_file.read())

# We are done

shutil.rmtree(mathjax_tmp_dir)
print('Install successful. Please restart Slack.')
sys.exit(0)


# References

# https://github.com/electron/node-chromium-pickle-js
# https://chromium.googlesource.com/chromium/src/+/master/base/pickle.h
# https://github.com/electron/asar
# https://github.com/electron-archive/node-chromium-pickle
# https://github.com/leovoel/BeautifulDiscord/tree/master/beautifuldiscord
