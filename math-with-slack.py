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
import stat
import errno
import platform
import glob
import plistlib
import shutil
import sys
import subprocess
import time
import textwrap
import logging
import math
import struct
import functools
import hashlib

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

mws_version = '0.4.3.0'

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


def get_platform():
  _platform = sys.platform
  if _platform == "win32":
    return "win32"
  elif _platform.startswith("linux"):
    return "linux"
  elif _platform.startswith("darwin"):
    return "darwin"
  else:
    exprint("Unsupported platform {}".format(_platform))


def _diagnose_permission(ex, app_path):
  err_msg = ""
  platform = get_platform()
  if platform == "win32":
    if _windows_process_exists("slack.exe"):
      err_msg = ("Possibile fix:\n"
                 "\tSeems like your Slack is running. "
                 "Please close Slack and re-run the script.")
  elif platform == "linux":
    app_path = os.path.normpath(app_path)
    app_path_parts = os.path.split(os.sep)
    if "snap" in app_path_parts:
      err_msg = ("Possibile fix:\n"
                 "\tSeems like you have a Snap "
                 "install that this script might not support. "
                 "Please check README for more details.")
  elif platform == "darwin":
    if isinstance(ex, IOError) or isinstance(
        ex, OSError) and (ex.errno == errno.EPERM or ex.errno == errno.EACCES):
      err_msg = (
          "Possibile fix:\n"
          "\tSeems like you are using MacOS. "
          "Perhaps your Slack is installed through App Store?\n"
          "\tIf that's the case, "
          "you will need to use `sudo` to give the script enough permissions. "
          "Please check README for more details.")
  return err_msg


def _macos_get_slack_app_root_path(app_path):
  return os.path.normpath(os.path.join(app_path, "../../../"))


def check_app_ready(app_path):
  plat = get_platform()
  if plat == "darwin":
    output = subprocess.check_output(
        ["xattr", _macos_get_slack_app_root_path(app_path)])
    if b'com.apple.appstore.metadata' in output:
      exprint("Cannot use this script on Slack downloaded from App Store."
              " Please re-install from Slack website instead.")


def check_permission(file_path, write=False):
  """Test if the file is readable and/or writable."""
  try:
    with open(file_path, mode='rb') as check_app_fp:
      app_content_bk = check_app_fp.read()

    if write:
      with open(file_path, mode='wb') as check_app_fp_w:
        check_app_fp_w.write(app_content_bk)

  except Exception as ex:
    print(ex)
    diagnosis = _diagnose_permission(ex, file_path)
    exprint(("Cannot modify {}. "
             "Make sure the script has write permissions. {}").format(
                 file_path, diagnosis))


def get_backup_path(orig_path):
  return orig_path + ".mwsbak"


def make_backup(orig_path):
  """Creates a backup."""
  backup_path = get_backup_path(orig_path)
  try:
    shutil.copy(orig_path, backup_path)
  except Exception as ex:
    print(ex)
    diagnosis = _diagnose_permission(ex, orig_path)
    exprint(("Cannot make backup {} -> {}. "
             "Make sure the script has write permissions. "
            ).format(orig_path, backup_path) + diagnosis)


def restore_from_backup(orig_file):
  """Restores backup into orig_file.
  
  Assumes write permission are set on `orig_file`.
  """
  backup_path = get_backup_path(orig_file)
  if not os.path.isfile(backup_path):
    exprint(
        "Missing backup at {}. Please re-install Slack.".format(backup_path))

  try:
    os.remove(orig_file)
    shutil.move(backup_path, orig_file)
  except Exception as ex:
    print(ex)
    diagnosis = _diagnose_permission(ex, orig_file)
    exprint(("Cannot remove previously modified file at {}. " +
             "Make sure the script has write permissions. ").format(orig_file) +
            diagnosis)


def remove_backup(orig_file):
  backup_path = get_backup_path(orig_file)
  if os.path.isfile(backup_path):
    try:
      os.remove(backup_path)
    except Exception as ex:
      print(ex)
      diagnosis = _diagnose_permission(ex, backup_path)
      exprint(
          ("Cannot remove old backup at {}. "
           "Make sure the script has write permissions.").format(backup_path) +
          diagnosis)


def macos_codesign_setup(cert, workdir):
  """Setup a certificate in MacOS's keychain."""

  out = subprocess.call(
      [
          "security", "find-certificate", "-Z", "-p", "-c", cert,
          "/Library/Keychains/System.keychain"
      ],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  if out == 0:
    print("Using existing certificate {}".format(cert))
    return
  cert_tmpl_path = os.path.join(workdir, "cert.tmpl")

  with open(cert_tmpl_path, "w+") as f:
    f.write(
        textwrap.dedent("""\
          [ req ]
          default_bits       = 2048        # RSA key size
          encrypt_key        = no          # Protect private key
          default_md         = sha512      # MD to use
          prompt             = no          # Prompt for DN
          distinguished_name = codesign_dn # DN template
          [ codesign_dn ]
          commonName         = "{}"
          [ codesign_reqext ]
          keyUsage           = critical,digitalSignature
          extendedKeyUsage   = critical,codeSigning""".format(cert)))

  print("Generating and installing {} certificate".format(cert))
  cert_path = os.path.join(workdir, "{}.cer".format(cert))
  key_path = os.path.join(workdir, "{}.key".format(cert))

  subprocess.check_call(
      [
          "openssl", "req", "-new", "-newkey", "rsa:2048", "-x509", "-days",
          "3650", "-nodes", "-config", cert_tmpl_path, "-extensions",
          "codesign_reqext", "-batch", "-out", cert_path, "-keyout", key_path
      ],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )

  subprocess.check_call(
      [
          "sudo", "security", "add-trusted-cert", "-d", "-r", "trustRoot", "-p",
          "codeSign", "-k", "/Library/Keychains/System.keychain", cert_path
      ],
      stdout=subprocess.DEVNULL,
  )

  subprocess.check_call(
      [
          "sudo", "security", "import", key_path, "-A", "-k",
          "/Library/Keychains/System.keychain"
      ],
      stdout=subprocess.DEVNULL,
  )

  subprocess.check_call(["sudo", "pkill", "-f", "/usr/libexec/taskgated"],
                        stdout=subprocess.DEVNULL)

  print("Geneterated new certificate {}".format(cert))


def macos_codesign_app(cert, workdir, app_path):
  slack_app_path = _macos_get_slack_app_root_path(app_path)
  entitlements_path = os.path.join(workdir, "slack-entitlements.xml")
  subprocess.check_call(
      ["codesign", "-d", "--entitlements", entitlements_path, slack_app_path],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  with open(entitlements_path, "r+") as f:
    is_der_file = "[Dict]" in f.readline()
    if is_der_file:
      # `codesign` produced a DER file, so scratch that and regenerate with `--xml`.
      f.truncate(0)
  if is_der_file:
    subprocess.check_call(
        [
            "codesign", "-d", "--entitlements", entitlements_path, "--xml",
            slack_app_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

  subprocess.check_call(
      [
          "codesign", "--entitlements", entitlements_path, "--force", "--sign",
          cert, slack_app_path
      ],
      stdout=subprocess.DEVNULL,
  )


# end Misc functions

# Asar


def roundup(val, divisor):
  return int(math.ceil((float(val) / divisor)) * divisor)


def is_unpacked(fileinfo):
  return fileinfo.get('unpacked', False)


def _walk_fileinfos(fileinfos, root=".", ignore_unpacked=False):
  for name, fileinfo in fileinfos["files"].items():
    sub_path = os.path.join(root, name)
    if 'files' in fileinfo:
      # is directory
      for v in _walk_fileinfos(fileinfo, root=sub_path):
        yield v
    elif ignore_unpacked and is_unpacked(fileinfo):
      continue
    else:
      yield sub_path, fileinfo


class AsarExtractor:
  """Represents a single *.asar file."""

  LOGGER = logging.getLogger("AsarExtractor")

  def __init__(self, filename, asarfile, files, baseoffset):
    """Initializes a new instance of the :see AsarExtractor class.
    Args:
        filename (str):
            The path to the *.asar file to read/write from/to.
        asarfile (File):
            An open *.asar file object.
        files (dict):
            Dictionary of files contained in the archive.
            (The header that was read from the file).
        baseoffset (int):
            Base offset, indicates where in the file the header ends.
    """
    self.filename = filename
    self.asarfile = asarfile
    self.files = files
    self.baseoffset = baseoffset

  def extract(self, destination):
    """Extracts the contents of the archive to the specifed directory.
    Args:
        destination (str):
            Path to an empty directory to extract the files to.
    """

    if os.path.exists(destination):
      raise OSError(20, 'Destination exists', destination)

    self.__extract_directory('.', self.files['files'], destination)

  def __extract_directory(self, path, files, destination):
    """Extracts a single directory to the specified directory on disk.
    Args:
        path (str):
            Relative (to the root of the archive) path of the directory
            to extract.
        files (dict):
            A dictionary of files from a *.asar file header.
        destination (str):
            The path to extract the files to.
    """

    # assures the destination directory exists
    destination_path = os.path.join(destination, path)
    if not os.path.exists(destination_path):
      os.makedirs(destination_path)
    for name, contents in files.items():
      item_path = os.path.join(path, name)

      # objects that have a 'files' member are directories,
      # recurse into them
      if 'files' in contents:
        self.__extract_directory(item_path, contents['files'], destination)

        continue

      self.__extract_file(item_path, contents, destination)

  def __extract_file(self, path, fileinfo, destination):
    """Extracts the specified file to the specified destination.
    Args:
        path (str):
            Relative (to the root of the archive) path of the
            file to extract.
        fileinfo (dict):
            Dictionary containing the offset and size of the file
            (Extracted from the header).
        destination (str):
            Directory to extract the archive to.
    """
    if is_unpacked(fileinfo):
      self.__copy_unpacked(path, destination)
      return

    self.asarfile.seek(self.__absolute_offset(fileinfo['offset']))

    # TODO: read in chunks, ain't going to read multiple GB's in memory
    contents = self.asarfile.read(fileinfo['size'])

    destination_path = os.path.join(destination, path)

    with open(destination_path, 'wb') as fp:
      fp.write(contents)

    if sys.platform != 'win32' and fileinfo.get('executable', False):
      os.chmod(destination_path,
               os.stat(destination_path).st_mode | stat.S_IEXEC)

    self.LOGGER.debug('Extracted %s to %s', path, destination_path)

  def __copy_unpacked(self, path, destination):
    """Copies a file that was already extracted to the destination directory.
    Args:
        path (str):
            Relative (to the root of the archive) of the file to copy.
        destination (str):
            Directory to extract the archive to.
    """

    unpacked_dir = self.filename + '.unpacked'
    if not os.path.isdir(unpacked_dir):
      self.LOGGER.warn('Failed to copy extracted file %s, no extracted dir',
                       path)

      return

    source_path = os.path.join(unpacked_dir, path)

    if not os.path.exists(source_path):
      self.LOGGER.warn('Failed to copy extracted file %s, does not exist', path)

      return

    destination_path = os.path.join(destination, path)
    shutil.copyfile(source_path, destination_path)

  def __absolute_offset(self, offset):
    """Converts the specified relative offset into an absolute offset.
    
    Offsets specified in the header are relative to the end of the header.
    Args:
        offset (int):
            The relative offset to convert to an absolute offset.
    Returns (int):
        The specified relative offset as an absolute offset.
    """

    return int(offset) + self.baseoffset

  def get_unpackeds(self):
    """Gets all the unpacked files."""
    for path, fileinfo in _walk_fileinfos(self.files, root="."):
      if is_unpacked(fileinfo):
        yield os.path.relpath(path, ".")

  def __enter__(self):
    """When the `with` statements opens."""

    return self

  def __exit__(self, type, value, traceback):
    """When the `with` statement ends."""

    if not self.asarfile:
      return

    self.asarfile.close()
    self.asarfile = None

  @classmethod
  def open(cls, filename):
    """Opens a *.asar file and constructs a new :see AsarArchive instance.
    
    Args:
        filename (str):
            Path to the *.asar file to open for reading.

    Returns (AsarArchive):
        An insance of of the :AsarArchive class or None if reading failed.
    """

    asarfile = open(filename, 'rb')

    (header_data_size, json_binary_size, json_data_size,
     json_string_size) = struct.unpack('<4I', asarfile.read(16))
    assert header_data_size == 4
    assert json_binary_size == json_data_size + 4
    json_header_bytes = asarfile.read(json_string_size).decode('utf-8')
    files = json.loads(json_header_bytes)
    baseoffset = roundup(16 + json_string_size, 4)
    return cls(filename, asarfile, files, baseoffset)


class AsarPacker:

  BLOCK_SIZE = 4 * 1024 * 1024

  def __dir_to_fileinfos(self, directory, unpackeds=tuple()):
    fileinfos = {'.': {'files': {}}}
    offset = 0
    for root, subdirs, files in os.walk(directory, topdown=True):
      parts = os.path.normpath(os.path.relpath(root,
                                               directory)).split(os.path.sep)
      if root != directory:
        parts = ['.'] + parts
      dirinfo = functools.reduce(lambda dirinfo, part: dirinfo[part]['files'],
                                 parts, fileinfos)
      for file in files:
        file_path = os.path.join(root, file)
        file_size = os.path.getsize(file_path)
        if os.path.relpath(file_path, directory) in unpackeds:
          fileinfo = {'size': file_size, 'unpacked': True}
        else:
          fileinfo = {'size': file_size, 'offset': str(offset)}
          offset += file_size
        if sys.platform != 'win32' and (os.stat(file_path).st_mode & 0o100):
          fileinfo['executable'] = True
        dirinfo[file] = fileinfo

      for subdir in subdirs:
        dirinfo[subdir] = {'files': {}}

    fileinfos = fileinfos['.']

    self.__add_file_integrities(directory, fileinfos)
    return fileinfos

  def pack(self, directory, out_asar, unpackeds=tuple()):
    """Pack a directory into an ASAR file.
    
    Args:
      directory (str): the directory to pack.
      out_asarfile (str): the output asar file path.
      unpackeds: (Tuple[str]): a list of files to ignore during packing.
    
    Returns:
      the hash of the header.
    """
    with open(out_asar, "wb") as out_asarfile:
      fileinfos = self.__dir_to_fileinfos(directory, unpackeds=unpackeds)
      json_header = json.dumps(fileinfos, sort_keys=True, separators=(',', ':'))
      json_header_bytes = json_header.encode('utf-8')
      header_string_size = len(json_header_bytes)
      data_size = 4
      aligned_size = roundup(header_string_size, data_size)
      header_size = aligned_size + 8
      header_object_size = aligned_size + data_size
      out_asarfile.seek(0)
      out_asarfile.write(
          struct.pack('<4I', data_size, header_size, header_object_size,
                      header_string_size))
      out_asarfile.write(json_header_bytes + b'\0' *
                         (aligned_size - header_string_size))
      baseoffset = roundup(header_string_size + 16, 4)
      for path, fileinfo in _walk_fileinfos(fileinfos, ignore_unpacked=True):
        with open(os.path.join(directory, path), 'rb') as fp:
          out_asarfile.seek(int(fileinfo['offset']) + baseoffset)
          out_asarfile.write(fp.read())
      return hashlib.sha256(json_header_bytes).hexdigest()

  def __add_file_integrities(self, directory, fileinfos):
    for path, fileinfo in _walk_fileinfos(fileinfos, ignore_unpacked=True):
      fileinfo["integrity"] = self.__get_file_integrity(
          os.path.join(directory, path))

  def __get_file_integrity(self, file):
    """Computes file integrity hashes of a file.
    
    For more details, see 
    https://paper.dropbox.com/doc/Electron-ASAR-Integrity-QrEbSA149226qARwYOcp9.

    Args:
      file (str): the full path to the file.
    
    Returns:
      a Dict, respecting Asar's integrity format.
    """
    hasher = hashlib.sha256()
    block_hashes = []
    with open(file, "rb") as f:
      while True:
        block = f.read(self.BLOCK_SIZE)
        if not block:
          break
        block_hashes.append(hashlib.sha256(block).hexdigest())
        hasher.update(block)
    return {
        "algorithm": "SHA256",
        "hash": hasher.hexdigest(),
        "blockSize": self.BLOCK_SIZE,
        "blocks": block_hashes
    }


# end Asar


def create_cmd_parser():
  parser = argparse.ArgumentParser(prog='math-with-slack',
                                   description='Inject Slack with MathJax.')
  parser.add_argument('-a',
                      '--app-file',
                      help='Path to Slack\'s \'app.asar\' file.')
  parser.add_argument(
      '--mathjax-url',
      help=("Either a remote URL to download a MathJax release or"
            " a local path to a pre-downloaded MathJax release."),
      default='https://registry.npmjs.org/mathjax/-/mathjax-3.1.0.tgz')
  parser.add_argument(
      '--mathjax-tex-options',
      type=str,
      help=('Path to file with TeX input processor options, '
            'or an inline string to the TeX input processor options. '
            'See http://docs.mathjax.org/en/latest/options/input/tex.html '
            'for the options format.'),
      default='default')
  parser.add_argument("--macos-codesign",
                      action="store_true",
                      help="Opt-in to perform code signing on MacOS.")
  parser.add_argument('-u',
                      '--uninstall',
                      action='store_true',
                      help='Removes injected MathJax code.')
  parser.add_argument('--version',
                      action='version',
                      version='%(prog)s ' + mws_version)
  return parser


# Find path to app.asar


def _find_candidate_app_files(path_globs,
                              filename="app*.asar",
                              min_file_size_kb=100):
  candidates = []
  for path_glob in path_globs:
    candidates += glob.glob(os.path.join(path_glob, filename))
  candidates = [
      c for c in candidates
      if os.path.isfile(c) and os.path.getsize(c) > min_file_size_kb * 1000
  ]
  candidates = sorted(candidates,
                      key=lambda c: os.path.getctime(c),
                      reverse=True)
  return candidates


def _filter_candidates_app_files_by_arch(search_paths):
  machine = platform.machine()
  if machine == "x86_64":
    suffix = "x64"
  else:
    suffix = "arm64"

  def cond(path):
    basename = os.path.splitext(os.path.basename(path))[0]
    return basename in ("app", "app-{}".format(suffix))

  return list(filter(cond, search_paths))


def _display_choose_from_menu(candidates, header="", prompt=""):
  print(header)
  for i, candidate in enumerate(candidates):
    if i == 0:
      candidate += " <== (default)"
    print("{}) {}".format(i, candidate))
  choice = input(prompt).lower()
  choice = "".join(choice.split())  # remote whitespace
  choice = choice.strip(")")  # remove trailing ')'
  try:
    if choice in ("", "y", "yes"):
      choice = 0
    else:
      choice = int(choice)
    return candidates[choice]
  except:
    exprint("Invalid choice. Please restart script.")


def resolve_app_path(app_path):
  """Resolves the true app_path from various sources of information."""
  if app_path is not None:
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
        'win32': ['c:\\Users\\*\\AppData\\Local\\slack\\*\\resources\\']
    }
    _platform = get_platform()
    search_paths = path_lookups[_platform]
    candidate_app_asars = _find_candidate_app_files(search_paths)
    if _platform == "darwin":
      candidate_app_asars = _filter_candidates_app_files_by_arch(
          candidate_app_asars)
    if len(candidate_app_asars) == 0:
      exprint(
          ("Could not find Slack's app.asar file under {}. "
           "Please manually provide path (see --help)").format(search_paths))
    if len(candidate_app_asars) == 1:
      app_path = candidate_app_asars[0]
    else:
      app_path = _display_choose_from_menu(
          candidate_app_asars,
          header="Several versions of Slack are installed.",
          prompt="Choose from above:")

  return app_path


def get_files_need_modification(app_path, slack_version):
  ret = [app_path]
  if get_platform() == "darwin" and slack_version >= LooseVersion("4.22"):
    ret += macos_get_plists(app_path)
  return ret


def is_previously_modified(app_path):
  with AsarExtractor.open(app_path) as asar_extractor:
    asar_header = asar_extractor.files
  return 'MWSINJECT' in asar_header["files"]


def extract_asar(tmp_dir, app_path):
  asar_extracted_dir = os.path.join(tmp_dir, "app.asar.unpacked")
  asar_extractor = AsarExtractor.open(app_path)
  asar_extractor.filename = app_path  # Use the non-backup asar name
  asar_extractor.extract(asar_extracted_dir)
  return asar_extractor, asar_extracted_dir


def read_slack_version(asar_extracted_dir):
  with open(os.path.join(asar_extracted_dir, "package.json"), "r") as f:
    return LooseVersion(json.load(f)["version"])


def check_slack_version(asar_extracted_dir):
  slack_version = read_slack_version(asar_extracted_dir)
  if slack_version <= LooseVersion('4.4'):
    exprint("Unsupported Slack Version {}.".format(slack_version))


def download_mathjax(mathjax_url):
  """Downloads MathJax and returns the core source.
  
  We currently assumes downloaded file is a tar called `package.tar`.
  """

  def get_reporthook():

    class report:
      start_time = None
      progress_size = None

    def reporthook(count, block_size, total_size):
      if count == 0:
        report.progress_size = 0
        report.start_time = time.time(
        ) - 1e-6  # also offset a bit so we don't run into divide by zero.
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
      sys.stdout.write(
          ("\rDownloading MathJax...{:3d}%, {:3.1f} MB / {:3.1f} MB,"
           " {:6.1f} KB/s, {:3.1f} sec").format(
               percent, report.progress_size / (1024 * 1024),
               total_size / (1024 * 1024), speed, duration))
      if report.progress_size >= total_size:
        sys.stdout.write("\n")
      sys.stdout.flush()

    return reporthook

  if os.path.isfile(mathjax_url):
    mathjax_tar_name = mathjax_url
  else:
    mathjax_tar_name, headers = urllib_request.urlretrieve(
        mathjax_url, [], get_reporthook())
  mathjax_tmp_dir = tempfile.mkdtemp()
  mathjax_tar = tarfile.open(mathjax_tar_name)
  mathjax_tar.extractall(path=mathjax_tmp_dir)
  mathjax_tar.close()
  mathjax_dir = os.path.join(mathjax_tmp_dir, "package")
  mathjax_src_path = os.path.join(mathjax_dir, "es5/tex-svg-full.js")
  with open(mathjax_src_path, "r+") as mathjax_src_file:
    mathjax_src = mathjax_src_file.read().encode('utf-8')
  return mathjax_src


def get_injected_code(mathjax_src, mathjax_tex_options):
  """Gets the injected code."""

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

  if mathjax_tex_options == "default":
    mathjax_tex_options = """{
        packages: {'[+]': ['noerrors', 'noundefined']},
        inlineMath: [['$', '$']],
        displayMath: [['$$', '$$']],
      }"""
  elif os.path.isfile(mathjax_tex_options):
    with open(mathjax_tex_options, "r") as f:
      mathjax_tex_options = f.read()
  else:
    mathjax_tex_options = mathjax_tex_options
  inject_code = inject_code.replace(b"$MATHJAX_TEX_OPTIONS$",
                                    mathjax_tex_options.encode("utf-8"))

  inject_code = inject_code.replace(b"$MATHJAX_STUB$", mathjax_src)
  return inject_code


def macos_get_plists(app_path):
  plist_paths = [
      "../../Info.plist",
      # "../../FrameWorks/Electron Framework.framework/Resources/Info.plist",
  ]
  return [os.path.normpath(os.path.join(app_path, p)) for p in plist_paths]


def macos_update_plists(app_path, new_asar_hash):
  """Given a path to app.asar, edit all the necessary plist files relative."""

  try:
    read_plist = plistlib.load
  except:
    read_plist = plistlib.readPlist

  try:
    write_plist = plistlib.dump
  except:
    write_plist = plistlib.writePlist

  for plist_path in macos_get_plists(app_path):
    with open(plist_path, "rb") as f:
      plist = read_plist(f)
    try:
      plist["ElectronAsarIntegrity"][os.path.relpath(
          app_path, os.path.join(app_path, "../.."))]["hash"] = new_asar_hash
    except KeyError:
      exprint("It appears that you likely have a broken Slack install. "
              "Please re-install Slack.")
    with open(plist_path, "wb") as f:
      write_plist(plist, f)


def macos_do_or_warn_codesign(do_codesign, workdir, app_path):
  codesign_msg = (
      "Math-with-slack is likely functional; "
      "however, you might experience log-offs if you quit Slack. "
      "See github.com/thisiscam/math-with-slack/issues/30 for more info.")
  if do_codesign:
    cert = "math-with-slack-codesign"
    try:
      macos_codesign_setup(cert, workdir)
      macos_codesign_app(cert, workdir, app_path)
    except:
      print("Warning: code signing failed. " + codesign_msg)
  else:
    print("Caveat!!!")
    print("You are on MacOS but have not enabled code signing. " +
          codesign_msg + "\n" + "If you don't understand the above, "
          "you should stop reading and use the script as-is, "
          "or uninstall the script with `--uninstall`." + "\n" +
          "If you know what this is about and know what you are doing: "
          "you may re-run this script with `--macos-codesign` "
          "to enable code signing. ")


def main():
  parser = create_cmd_parser()
  args = parser.parse_args()

  platform = get_platform()

  app_path = resolve_app_path(args.app_file)
  print('Using Slack installation at: ' + app_path)

  check_app_ready(app_path)
  check_permission(app_path, write=False)

  tmp_dir = tempfile.mkdtemp()
  _, asar_extracted_dir = extract_asar(tmp_dir, app_path)
  slack_version = read_slack_version(asar_extracted_dir)
  shutil.rmtree(asar_extracted_dir)
  files_to_modify = get_files_need_modification(app_path, slack_version)

  for file in files_to_modify:
    check_permission(file, write=True)

  if is_previously_modified(app_path):
    for file in files_to_modify:
      restore_from_backup(file)

  for file in files_to_modify:
    remove_backup(file)

  if args.uninstall:
    print('Uninstall successful. Please restart Slack.')
    sys.exit(0)

  for file in files_to_modify:
    make_backup(file)

  asar_extractor, asar_extracted_dir = extract_asar(tmp_dir, app_path)
  assert 'MWSINJECT' not in asar_extractor.files["files"]

  check_slack_version(asar_extracted_dir)
  mathjax_src = download_mathjax(args.mathjax_url)
  inject_code = get_injected_code(mathjax_src, args.mathjax_tex_options)

  with open(os.path.join(asar_extracted_dir, "MWSINJECT"), "w") as f:
    pass

  with open(os.path.join(asar_extracted_dir, "dist/preload.bundle.js"),
            "ab") as f:
    f.write(inject_code)

  asar_packer = AsarPacker()
  new_asar_hash = asar_packer.pack(asar_extracted_dir, app_path,
                                   asar_extractor.get_unpackeds())

  if platform == "darwin" and slack_version >= LooseVersion("4.22"):
    macos_update_plists(app_path, new_asar_hash)
    macos_do_or_warn_codesign(args.macos_codesign, tmp_dir, app_path)

  shutil.rmtree(tmp_dir)
  print('Install successful. Please restart Slack.')
  sys.exit(0)


if __name__ == '__main__':
  main()

# References
#
# https://github.com/electron/node-chromium-pickle-js
# https://chromium.googlesource.com/chromium/src/+/master/base/pickle.h
# https://github.com/electron/asar
# https://github.com/electron-archive/node-chromium-pickle
# https://github.com/leovoel/BeautifulDiscord/tree/master/beautifuldiscord
# https://github.com/Photonios/pyasar
