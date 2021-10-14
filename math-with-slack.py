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
import errno
import platform
import glob
import shutil
import struct
import sys
import subprocess
import time
from distutils.version import LooseVersion

try:
    # Python 3
    import urllib.request as urllib_request
except:
    # Python 2
    import urllib as urllib_request
# ssl is added for Windows and possibly Mac to avoid ssl
# certificate_verify_failed error
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import tarfile
import tempfile


# Math with Slack version

mws_version = '0.4.2.0'


# Parse command line options

parser = argparse.ArgumentParser(prog='math-with-slack', description='Inject Slack with MathJax.')
parser.add_argument('-a', '--app-file', help='Path to Slack\'s \'app.asar\' file.')
parser.add_argument('--mathjax-url', 
                    help='Either a remote URL to download a MathJax release or a local path to a pre-downloaded MathJax release.', 
                    default='https://registry.npmjs.org/mathjax/-/mathjax-3.1.0.tgz')
parser.add_argument('--mathjax-tex-options', 
                    type=str,
                    help='Path to file with TeX input processor options, '
                         'or an inline string to the TeX input processor options. '
                         'See http://docs.mathjax.org/en/latest/options/input/tex.html for the options format.', 
                    default='default')
parser.add_argument('-u', '--uninstall', action='store_true', help='Removes injected MathJax code.')
parser.add_argument('--version', action='version', version='%(prog)s ' + mws_version)
args = parser.parse_args()


# Misc functions

def exprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.exit(1)


def _windows_process_exists(process_name):
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())

def _diagnose_permission(e, app_path):
    err_msg = ""
    if sys.platform == "win32":
        if _windows_process_exists("slack.exe"):
            err_msg = ("Possibile fix:\n"
                       "\tSeems like your Slack is running. "
                       "Please close Slack and re-run the script.")
    elif sys.platform.startswith("linux"):
        app_path = os.path.normpath(app_path)
        app_path_parts = os.path.split(os.sep)
        if "snap" in app_path_parts:
            err_msg = ("Possibile fix:\n"
                       "\tSeems like you have a Snap install that this script might not support. "
                       "Please check README for more details.")
    elif sys.platform.startswith("darwin"):
        if isinstance(e, IOError) or isinstance(e, OSError) and (e.errno == errno.EPERM or e.errno == errno.EACCES):
            err_msg = ("Possibile fix:\n"
                       "\tSeems like you are using MacOS. Perhaps your Slack is installed through App Store?\n"
                       "\tIf that's the case, you will need to use `sudo` to give the script enough permissions. "
                       "Please check README for more details.")
    return err_msg


# Find path to app.asar

def find_candidate_app_files(path_globs, filename="app*.asar", min_file_size_kb=100):
    candidates = []
    for path_glob in path_globs:
        candidates += glob.glob(os.path.join(path_glob, filename))
    candidates =[c for c in candidates 
        if os.path.isfile(c) and os.path.getsize(c) > min_file_size_kb * 1000]
    candidates = sorted(candidates, key=lambda c: os.path.getctime(c), reverse=True)
    return candidates


def filter_candidates_app_files_by_arch(search_paths):
    machine = platform.machine()
    if machine == "x86_64":
        suffix = "x64"
    else:
        suffix = "arm64"

    def cond(path):
        basename = os.path.splitext(os.path.basename(path))[0]
        return basename in ("app", "app-{}".format(suffix))

    return list(filter(cond, search_paths))


def display_choose_from_menu(candidates, header="", prompt=""):
    print(header)
    for i, candidate in enumerate(candidates):
        if i == 0:
            candidate += " <== (default)"
        print("{}) {}".format(i, candidate))
    choice = input(prompt).lower()
    choice = "".join(choice.split()) # remote whitespace
    choice = choice.strip(")") # remove trailing ')'
    try:
        if choice in ("", "y", "yes"):
            choice = 0
        else:
            choice = int(choice)
        return candidates[choice]
    except:
        exprint("Invalid choice. Please restart script.")


if args.app_file is not None:
    app_path = args.app_file
    if not os.path.isfile(app_path):
        exprint('Cannot find Slack at ' + app_path)
else:
    path_lookups = {
        'darwin': ['/Applications/Slack.app/Contents/Resources/'],
        'linux': [
            '/usr/lib/slack/resources/',
            '/usr/local/lib/slack/resources/',
            '/opt/slack/resources/',
            '/mnt/c/Users/*/AppData/Local/slack/*/resources/',
        ],
        'win32': [
            'c:\\Users\\*\\AppData\\Local\\slack\\*\\resources\\'
        ]
    }
    _platform = sys.platform
    if _platform.startswith('linux'):
        _platform = 'linux'
    search_paths = path_lookups[_platform]
    candidate_app_asars = find_candidate_app_files(search_paths)
    if _platform == "darwin":
        candidate_app_asars = filter_candidates_app_files_by_arch(candidate_app_asars)
    if len(candidate_app_asars) == 0:
        exprint(("Could not find Slack's app.asar file under {}. "
                 "Please manually provide path (see --help)").format(search_paths))
    if len(candidate_app_asars) == 1:
        app_path = candidate_app_asars[0]
    else: 
        app_path = display_choose_from_menu(candidate_app_asars, 
            header="Several versions of Slack are installed.", 
            prompt="Choose from above:")


# Print info
print('Using Slack installation at: ' + app_path)


# Remove previously injected code if it exists

with open(app_path, mode='rb') as check_app_fp:
    (header_data_size, json_binary_size) = struct.unpack('<II', check_app_fp.read(8))
    assert header_data_size == 4
    json_binary = check_app_fp.read(json_binary_size)

# Do round trip write back to test if the file is writable...
with open(app_path, mode='rb') as check_app_fp:
    app_content_bk = check_app_fp.read()
try:
    with open(app_path, mode='wb') as check_app_fp_w:
        check_app_fp_w.write(app_content_bk)
except Exception as e:
    print(e)
    diagnosis = _diagnose_permission(e, app_path)
    exprint('Cannot inject code to {}. Make sure the script has write permissions. {}'.format(app_path, diagnosis))


(json_data_size, json_string_size) = struct.unpack('<II', json_binary[:8])
assert json_binary_size == json_data_size + 4
json_check = json.loads(json_binary[8:(json_string_size + 8)].decode('utf-8'))

app_backup_path = app_path + '.mwsbak'

if 'MWSINJECT' in json_check['files']:
    if not os.path.isfile(app_backup_path):
        exprint('Found injected code without backup. Please re-install Slack.')
    try:
        os.remove(app_path)
        shutil.move(app_backup_path, app_path)
    except Exception as e:
        print(e)
        diagnosis = _diagnose_permission(e, app_path)
        exprint('Cannot remove previously injected code. Make sure the script has write permissions. ' + diagnosis)


# Remove old backup if it exists

if os.path.isfile(app_backup_path):
    try:
        os.remove(app_backup_path)
    except Exception as e:
        print(e)
        diagnosis = _diagnose_permission(e, app_backup_path)
        exprint('Cannot remove old backup. Make sure the script has write permissions. ' + diagnosis)


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

  function typeset(elements) {
    if(elements.length) {
        const MathJax = window.MathJax;
        MathJax.startup.promise = MathJax.startup.promise
          .then(() => { return MathJax.typesetPromise(elements); })
          .catch((err) => console.log('Typeset failed: ' + err.message));
        return MathJax.startup.promise;
    }
  }

  window.MathJax = {
    options: {
        skipHtmlTags: [
            'script', 'noscript', 'style', 'textarea', 'pre',
            'code', 'annotation', 'annotation-xml'
        ],
        renderActions: {
          assistiveMml: [], // Disable assitiveMML since we are not using it anywhere
                            // Also because this will cause duplicated copied text
          addCopyText: [156,
            (doc) => {
                if (!doc.processed.isSet('addtext')) {
                    for (const math of doc.math) {
                        MathJax.config.addCopyText(math, doc);
                    }
                    doc.processed.set('addtext');
                }
            },
            (math, doc) => MathJax.config.addCopyText(math, doc)
          ]
        }
    },
    addCopyText(math, doc) {
        if (math.state() < MathJax.STATE.ADDTEXT) {
            if (!math.isEscaped) {
                const adaptor = doc.adaptor;
                const text = adaptor.node('span', {'aria-hidden': true, 'class': 'mathjax_ignore mjx-copytext'}, [
                  adaptor.text(math.start.delim + math.math + math.end.delim)
                ]);
                adaptor.append(math.typesetRoot, text);
                // Insert thin space(s) if math is at begin or end of text
                if (math.start.n == 0) {
                    adaptor.insert(adaptor.text('\u200A'), adaptor.firstChild(math.typesetRoot));
                }
                if (math.end.n == math.end.node.length) {
                    adaptor.append(math.typesetRoot, adaptor.text('\u200A'));
                }
            }
            math.state(MathJax.STATE.ADDTEXT);
        }
    },
    loader: {
        paths: {mathjax: 'mathjax/es5'},
        source: {},
        require: require,
        load: [
            'input/tex-full',
            'output/svg',
            '[tex]/noerrors', 
            '[tex]/noundefined', 
        ]
    },
    tex: $MATHJAX_TEX_OPTIONS$,
    startup: {
      ready: () => {
        MathJax = window.MathJax;

        // Allocate a state bit for mjx-copytext and 
        // make the copyable text hidden
        const {newState, STATE} = MathJax._.core.MathItem;
        const {AbstractMathDocument} = MathJax._.core.MathDocument;
        const {SVG} = MathJax._.output.svg_ts;
        newState('ADDTEXT', 156);
        AbstractMathDocument.ProcessBits.allocate('addtext');
        SVG.commonStyles['.mjx-copytext'] = {
            'font-size': 0
        };
        MathJax.STATE = STATE;

        // Invoke MathJax's default initialization
        MathJax.startup.defaultReady();

        // Disable some menu option that will cause us to crash
        MathJax.startup.document.menu.menu.findID('Settings', 'Renderer').disable();
        MathJax.startup.document.menu.menu.findID('Accessibility').disable();

        // Observer for when an element needs to be typeset
        var intersection_observer = new IntersectionObserver(
          (entries, observer) => {
            var appearedEntries = entries.filter((entry) => entry.intersectionRatio > 0);
            if(appearedEntries.length) {
                typeset(appearedEntries.map((entry) => entry.target));
            }
          },
          { root: document.body }
        );

        // observer for elements are first inserted into the DOM.
        // We delay elements that require typesetting to the intersection observer
        function observe_dom_change(mutations) {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((addedNode) => {
                    if(addedNode.nodeType != Node.TEXT_NODE) {
                        const messages = addedNode.querySelectorAll(
                        'span.c-message__body, span.c-message_kit__text, div.p-rich_text_block, span.c-message_attachment__text');
                        messages.forEach((msg) => {
                            if(!msg.ready) {
                                msg.ready = true;
                                intersection_observer.observe(msg);
                            }
                        });
                    }
                });
            })
            mutations.forEach((mutation) => {
                MathJax.typesetClear(mutation.removedNodes);
            })
        }
        var mutation_observer = new MutationObserver(observe_dom_change);
        mutation_observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        observe_dom_change();
      }
    },
  };

  var ctxMenustyle = document.createElement('style');
  ctxMenustyle.innerHTML = `
  .CtxtMenu_MenuFrame {
    z-index: 10000 !important;
  }
  .CtxtMenu_Menu {
    z-index: 10000 !important;
  }
  .CtxtMenu_Info {
    z-index: 10000 !important;
  }
  `;
  document.body.appendChild(ctxMenustyle);

  // Import mathjax
  $MATHJAX_STUB$
});
''').encode('utf-8')

if args.mathjax_tex_options == "default": 
    mathjax_tex_options = """{
      packages: {'[+]': ['noerrors', 'noundefined']},
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']],
    }"""
elif os.path.isfile(args.mathjax_tex_options):
    with open(args.mathjax_tex_options, "r") as f:
        mathjax_tex_options = f.read()
else:
    mathjax_tex_options = args.mathjax_tex_options
inject_code = inject_code.replace(b"$MATHJAX_TEX_OPTIONS$", 
    mathjax_tex_options.encode("utf-8"))

# Make backup

try:
    shutil.copy(app_path, app_backup_path)
except Exception as e:
    print(e)
    diagnosis = _diagnose_permission(e, app_path)
    exprint("Cannot make backup. Make sure the script has write permissions. " + diagnosis)


# Get file info

with open(app_backup_path, mode='rb') as ori_app_fp:
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

def read_file_from_asar(file_offset, file_size):
    with open(app_backup_path, mode='rb') as ori_app_fp:
        ori_app_fp.seek(file_offset + ori_data_offset)
        binary = ori_app_fp.read(file_size)
        return binary

def read_package_json():
    package_json_desp = json_header['files']['package.json']
    binary = read_file_from_asar(int(package_json_desp['offset']), int(package_json_desp['size']))
    return json.loads(binary)

def read_slack_version():
    package_json = read_package_json()
    return LooseVersion(package_json['version'])

slack_version = read_slack_version()

if LooseVersion('4.3') <= slack_version < LooseVersion('4.4'):
    injected_file_name = 'main-preload-entry-point.bundle.js'
    include_mathjax_inline = False
elif LooseVersion('4.4') <= slack_version:
    injected_file_name = 'preload.bundle.js'
    include_mathjax_inline = True # We always use include mathjax inline now
else:
    exprint("Unsupported Slack Version {}.".format(slack_version))

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


ori_injected_file_size = json_header['files']['dist']['files'][injected_file_name]['size']
ori_injected_file_offset = int(json_header['files']['dist']['files'][injected_file_name]['offset'])

# Download MathJax, currently assumes downloaded file is a tar called package.tar
def get_reporthook():
    class report:
        start_time = None
        progress_size = None
    def reporthook(count, block_size, total_size):
        if count == 0:
            report.progress_size = 0
            report.start_time = time.time() - 1e-6 # also offset a bit so we don't run into divide by zero.
            return
        duration = time.time() - report.start_time
        report.progress_size += block_size
        if report.progress_size >= total_size:
            report.progress_size = total_size
        try:
            speed = report.progress_size / (1024 * duration)
            percent = int(report.progress_size * 100 / total_size)
        except ZeroDivisionError:
            speed, percent = 0, 0
        sys.stdout.write("\rDownloading MathJax...{:3d}%, {:3.1f} MB / {:3.1f} MB, {:6.1f} KB/s, {:3.1f} sec".format(
            percent, report.progress_size / (1024 * 1024), total_size / (1024 * 1024), speed, duration))
        if report.progress_size >= total_size:
            sys.stdout.write("\n")
        sys.stdout.flush()
    return reporthook

if os.path.isfile(args.mathjax_url):
    mathjax_tar_name = args.mathjax_url
else:
    mathjax_tar_name, headers = urllib_request.urlretrieve(args.mathjax_url, 
        [], get_reporthook())
mathjax_tmp_dir = tempfile.mkdtemp()
mathjax_tar = tarfile.open(mathjax_tar_name)
mathjax_tar.extractall(path=mathjax_tmp_dir)
mathjax_tar.close()
mathjax_dir = os.path.join(mathjax_tmp_dir, "package")
if include_mathjax_inline:
    mathjax_src_path = os.path.join(mathjax_dir, "es5/tex-svg-full.js")
    with open(mathjax_src_path, "r+") as mathjax_src_file:
        mathjax_src = mathjax_src_file.read().encode('utf-8')
    append_file_paths = []
else:
    mathjax_json_header, append_file_paths = dir_to_json_header(mathjax_dir, ori_data_size + ori_injected_file_size + len(inject_code))
    json_header["files"]["node_modules"]["files"]["mathjax"] = mathjax_json_header["files"]["."]
    mathjax_src = "require('mathjax/es5/startup.js');"

inject_code = inject_code.replace(b"$MATHJAX_STUB$", mathjax_src)

# Modify JSON data

json_header['files']['MWSINJECT'] = json_header['files']['LICENSE']
json_header['files']['dist']['files'][injected_file_name]['size'] = ori_injected_file_size + len(inject_code)
json_header['files']['dist']['files'][injected_file_name]['offset'] = str(ori_data_size)

# Write new app.asar file

new_json_header = json.dumps(json_header, separators=(',', ':')).encode('utf-8')
new_json_header_padding = (4 - len(new_json_header) % 4) % 4

with open(app_backup_path, mode='rb') as ori_app_fp, \
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
