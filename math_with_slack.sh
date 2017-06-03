#!/usr/bin/env bash

################################################################################
# Rendered math (MathJax) with Slack's desktop client
################################################################################
#
# Slack (https://slack.com) does not display rendered math. This script injects
# MathJax (https://www.mathjax.org) into Slack's desktop client, which allows
# you to write nice-looking inline- and display-style math using familiar
# TeX/LaTeX syntax. You can also edit equations after you've posted them.
#
# https://github.com/fsavje/math-with-slack
#
# MIT License, Copyright 2017 Fredrik Savje
#
################################################################################


## User input

for p in "$@"; do
	if [ "$p" = "-f" ]; then
		FORCE="$p"
	else
		SLACK_INDEX="$p"
	fi
done


## Platform settings

if [ "$(uname)" == "Darwin" ]; then
	# macOS
	SHASUM=shasum
	COMMON_INDEX_LOCATIONS=(
		"/Applications/Slack.app/Contents/Resources/app.asar.unpacked/src/static/index.js"
	)

	## If the user-provided "index.js" is not found, try to find it
	if [ -n "$SLACK_INDEX" ] && [ ! -e "$SLACK_INDEX" ]; then
		if [ -e "${SLACK_INDEX}Contents/Resources/app.asar.unpacked/src/static/index.js" ]; then
			SLACK_INDEX="${SLACK_INDEX}Contents/Resources/app.asar.unpacked/src/static/index.js"
		elif [ -e "$SLACK_INDEX/Contents/Resources/app.asar.unpacked/src/static/index.js" ]; then
			SLACK_INDEX="$SLACK_INDEX/Contents/Resources/app.asar.unpacked/src/static/index.js"
		fi
	fi

else
	# Linux
	SHASUM=sha1sum
	COMMON_INDEX_LOCATIONS=(
		"/usr/lib/slack/resources/app.asar.unpacked/src/static/index.js"
		"/usr/local/lib/slack/resources/app.asar.unpacked/src/static/index.js"
		"/opt/slack/resources/app.asar.unpacked/src/static/index.js"
	)

	## Repoint from binary to library
	if [ "$SLACK_INDEX" = "/usr/bin/slack" ]; then
		SLACK_INDEX="/usr/lib/slack/resources/app.asar.unpacked/src/static/index.js"
	elif [ "$SLACK_INDEX" = "/usr/local/bin/slack" ]; then
		SLACK_INDEX="/usr/local/lib/slack/resources/app.asar.unpacked/src/static/index.js"
	fi

	## If the user-provided "index.js" is not found, try to find it
	if [ -n "$SLACK_INDEX" ] && [ ! -e "$SLACK_INDEX" ]; then
		if [ -e "${SLACK_INDEX}resources/app.asar.unpacked/src/static/index.js" ]; then
			SLACK_INDEX="${SLACK_INDEX}resources/app.asar.unpacked/src/static/index.js"
		elif [ -e "$SLACK_INDEX/resources/app.asar.unpacked/src/static/index.js" ]; then
			SLACK_INDEX="$SLACK_INDEX/resources/app.asar.unpacked/src/static/index.js"
		fi
	fi

fi


## Try to find slack if not provided by user

if [ -z "$SLACK_INDEX" ]; then
	for file in "${COMMON_INDEX_LOCATIONS[@]}"; do
		if [ -e "$file" ]; then
			SLACK_INDEX="$file"
			break
		fi
	done
fi


## Check so "index.js" exists and is writable

if [ -z "$SLACK_INDEX" ]; then
	echo "Cannot find Slack's index file."
	exit 1
fi

if [ ! -e "$SLACK_INDEX" ]; then
	echo "Cannot find Slack's index file: $SLACK_INDEX"
	exit 1
fi

if [ ! -w "$SLACK_INDEX" ]; then
	echo "Cannot write to Slack's index file: $SLACK_INDEX"
	exit 1
fi


## Does backup exists? If so, do update

if [ -e "$SLACK_INDEX.mwsbak" ]; then
	cp -f $SLACK_INDEX.mwsbak $SLACK_INDEX
fi


## Check so "index.js" is known to work with the script

if [ -z "$FORCE" ]; then
	KNOWN_INDEX_HASHES=(
		"f8398ab83df1c69bc39a7a3f0ed4c5594a3d76de"
	)
	INDEX_HASH=$($SHASUM $SLACK_INDEX | cut -c 1-40)
	for hash in "${KNOWN_INDEX_HASHES[@]}"; do
		if [ "$INDEX_HASH" = "$hash" ]; then
			INDEX_HASH="ok"
			break
		fi
	done
	if [ "$INDEX_HASH" != "ok" ]; then
		echo "Unrecognized index file: $SLACK_INDEX"
		echo "Call with '-f' flag to suppress this check."
		exit 1
	fi
fi


## Ensure "index.js" contains "startup();"

if ! grep -q "^    startup();$" $SLACK_INDEX; then
	echo "Cannot find 'startup();' in index file: $SLACK_INDEX"
	exit 1
fi


## Does backup exists? If not, make one

if [ ! -e "$SLACK_INDEX.mwsbak" ]; then
	cp $SLACK_INDEX $SLACK_INDEX.mwsbak
fi


## Write code for MathJax injection

ed -s $SLACK_INDEX <<EOF > /dev/null
/startup();
a

    // *** Code injected for MathJax support
    // See: https://github.com/fsavje/math-with-slack

    var mathjax_inject_script = \`
      var mathjax_config = document.createElement("script");
      mathjax_config.type = "text/x-mathjax-config";
      mathjax_config.text = \\\`
        MathJax.Hub.Config({
          messageStyle: "none",
          extensions: ["tex2jax.js"],
          jax: ["input/TeX", "output/HTML-CSS"],
          tex2jax: {
            skipTags: ["script","noscript","style","textarea","pre","code"],
            ignoreClass: "ql-editor",
            inlineMath: [ ['\$','\$'] ],
            displayMath: [ ['\$\$','\$\$'] ],
            processEscapes: true
          },
          TeX: {
            extensions: ["AMSmath.js", "AMSsymbols.js", "noErrors.js", "noUndefined.js"]
          }
        });
        \\\`;
      var mathjax_script = document.createElement("script");
      mathjax_script.type = "text/javascript";
      mathjax_script.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.0/MathJax.js";
      document.getElementsByTagName("head")[0].appendChild(mathjax_config);
      document.getElementsByTagName("head")[0].appendChild(mathjax_script);

      var render = function (records, observer) {
          MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
      };
      var target = document.querySelector('#msgs_div');
      var observer = new MutationObserver(render);
      var config = { attributes: false, childList: true, characterData: true, subtree: true };
      observer.observe(target, config);
    \`;

    window.webviews = document.querySelectorAll(".TeamView webview");
    setTimeout(function() {
      for(var i = 0; i < webviews.length; i++) {
        webviews[i].executeJavaScript(mathjax_inject_script);
      }
    }, 20000);

    // *** End injected MathJax

.
w
q
EOF

echo "MathJax successfully injected into Slack. Please restart Slack client."
