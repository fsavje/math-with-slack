#!/bin/sh

# *** LaTeX Math (MathJax) with Slack's desktop client ***
#
# Slack does not support math. This shell script injects MathJax
# into Slack's desktop client. This allows you to write both
# inline- and display-style math. You can also edit equations
# after you've posted them.
#
# https://github.com/fsavje/math-with-slack
#
# MIT License

SLACK_INDEX="$1"

if [ -z "$SLACK_INDEX" ]; then
	SLACK_INDEX="/Applications/Slack.app/Contents/Resources/app.asar.unpacked/src/static/index.js"
fi

if [ ! -e "$SLACK_INDEX" ]; then
	echo "Cannot find Slack's index file: $SLACK_INDEX"
	exit 1
fi

if [ ! -w "$SLACK_INDEX" ]; then
	echo "Cannot write to Slack's index file: $SLACK_INDEX"
	exit 1
fi

# Backup
cp -f $SLACK_INDEX $SLACK_INDEX.bak

# Write code for MathJax injection
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
            inlineMath: [ ['\$','\$'] ],
            displayMath: [ ['\$\$','\$\$'] ],
            processEscapes: true
          },
          TeX: {
            extensions: ["noErrors.js", "noUndefined.js"]
          }
        });
        \\\`;
      var mathjax_script = document.createElement("script");
      mathjax_script.type = "text/javascript";
      mathjax_script.src = "https://cdn.mathjax.org/mathjax/latest/MathJax.js";
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
    }, 10000);

    // *** End injected MathJax

.
w
q
EOF
