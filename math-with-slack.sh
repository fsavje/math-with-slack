#!/usr/bin/env bash

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
# MIT License, Copyright 2017-2018 Fredrik Savje
#
################################################################################


## Constants

MWS_VERSION="v0.2.5"


## Functions

error() {
	echo "$(tput setaf 124)$(tput bold)✘ $1$(tput sgr0)"
	exit 1
}


## User input

for p in "$@"; do
	if [ "$p" = "-u" ]; then
		UNINSTALL="$p"
	else
		SLACK_DIR="$p"
	fi
done


## Platform settings

if [ "$(uname)" == "Darwin" ]; then
	# macOS
	COMMON_SLACK_LOCATIONS=(
		"/Applications/Slack.app/Contents/Resources/app.asar.unpacked/src/static"
	)
else
	# Linux
	COMMON_SLACK_LOCATIONS=(
		"/usr/lib/slack/resources/app.asar.unpacked/src/static"
		"/usr/local/lib/slack/resources/app.asar.unpacked/src/static"
		"/opt/slack/resources/app.asar.unpacked/src/static"
	)
fi


## Try to find slack if not provided by user

if [ -z "$SLACK_DIR" ]; then
	for loc in "${COMMON_SLACK_LOCATIONS[@]}"; do
		if [ -e "$loc" ]; then
			SLACK_DIR="$loc"
			break
		fi
	done
fi


## Files

SLACK_MATHJAX_SCRIPT="$SLACK_DIR/math-with-slack.js"
SLACK_SSB_INTEROP="$SLACK_DIR/ssb-interop.js"


## Check so installation exists and is writable

if [ -z "$SLACK_DIR" ]; then
	error "Cannot find Slack installation."
elif [ ! -e "$SLACK_DIR" ]; then
	error "Cannot find Slack installation at: $SLACK_DIR"
elif [ ! -e "$SLACK_SSB_INTEROP" ]; then
	error "Cannot find Slack file: $SLACK_SSB_INTEROP"
elif [ ! -w "$SLACK_SSB_INTEROP" ]; then
	error "Cannot write to Slack file: $SLACK_SSB_INTEROP"
fi

echo "Using Slack installation at: $SLACK_DIR"


## Remove previous version

if [ -e "$SLACK_MATHJAX_SCRIPT" ]; then
	rm $SLACK_MATHJAX_SCRIPT
fi


## Restore previous injections

# Check whether file been injected. If not, assume it's more recent than backup
if grep -q "math-with-slack" $SLACK_SSB_INTEROP; then
  if [ -e "$SLACK_SSB_INTEROP.mwsbak" ]; then
    mv -f $SLACK_SSB_INTEROP.mwsbak $SLACK_SSB_INTEROP
  else
    error "Cannot restore from backup. Missing file: $SLACK_SSB_INTEROP.mwsbak"
  fi
elif [ -e "$SLACK_SSB_INTEROP.mwsbak" ]; then
  rm $SLACK_SSB_INTEROP.mwsbak
fi


## Are we uninstalling?

if [ -n "$UNINSTALL" ]; then
	echo "$(tput setaf 64)math-with-slack has been uninstalled. Please restart the Slack client.$(tput sgr0)"
	exit 0
fi


## Write main script

cat <<EOF > $SLACK_MATHJAX_SCRIPT
// math-with-slack $MWS_VERSION
// https://github.com/fsavje/math-with-slack

document.addEventListener('DOMContentLoaded', function() {
  var mathjax_config = document.createElement('script');
  mathjax_config.type = 'text/x-mathjax-config';
  mathjax_config.text = \`
    MathJax.Hub.Config({
      messageStyle: 'none',
      extensions: ['tex2jax.js'],
      jax: ['input/TeX', 'output/HTML-CSS'],
      tex2jax: {
        displayMath: [['\$\$', '\$\$']],
        element: 'msgs_div',
        ignoreClass: 'ql-editor',
        inlineMath: [['\$', '\$']],
        processEscapes: true,
        skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      },
      TeX: {
        extensions: ['AMSmath.js', 'AMSsymbols.js', 'noErrors.js', 'noUndefined.js']
      }
    });
  \`;

  var mathjax_observer = document.createElement('script');
  mathjax_observer.type = 'text/x-mathjax-config';
  mathjax_observer.text = \`
    var target = document.querySelector('#messages_container');
    var options = { attributes: false, childList: true, characterData: true, subtree: true };
    var observer = new MutationObserver(function (r, o) { MathJax.Hub.Queue(['Typeset', MathJax.Hub]); });
    observer.observe(target, options);
  \`;

  var mathjax_script = document.createElement('script');
  mathjax_script.type = 'text/javascript';
  mathjax_script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js';

  document.head.appendChild(mathjax_config);
  document.head.appendChild(mathjax_observer);
  document.head.appendChild(mathjax_script);
});
EOF


## Inject code loader

# Check so not already injected
if grep -q "math-with-slack" $SLACK_SSB_INTEROP; then
  error "File already injected: $SLACK_SSB_INTEROP"
fi

# Make backup
if [ ! -e "$SLACK_SSB_INTEROP.mwsbak" ]; then
  cp $SLACK_SSB_INTEROP $SLACK_SSB_INTEROP.mwsbak
else
  error "Backup already exists: $SLACK_SSB_INTEROP.mwsbak"
fi

# Inject loader code
ed -s $SLACK_SSB_INTEROP <<EOF > /dev/null
/init(resourcePath, mainModule, !isDevMode);
i
  // ** math-with-slack $MWS_VERSION ** https://github.com/fsavje/math-with-slack
  var mwsp = path.join(__dirname, 'math-with-slack.js').replace('app.asar', 'app.asar.unpacked');
  require('fs').readFile(mwsp, 'utf8', (e, r) => { if (e) { throw e; } else { eval(r); } });

.
w
q
EOF


## We're done

echo "$(tput setaf 64)math-with-slack has been installed. Please restart the Slack client.$(tput sgr0)"
