@ECHO OFF

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Rendered math (MathJax) with Slack's desktop client
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Slack (https://slack.com) does not display rendered math. This script injects
:: MathJax (https://www.mathjax.org) into Slack's desktop client, which allows
:: you to write nice-looking inline- and display-style math using familiar
:: TeX/LaTeX syntax. You can also edit equations after you've posted them.
::
:: https://github.com/fsavje/math-with-slack
::
:: MIT License, Copyright 2017 Fredrik Savje
::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:: User input

SET "FORCE="
SET "SLACK_INDEX="

:parse
IF "%~1" == "" GOTO endparse
IF "%~1" == "-f" (
	SET FORCE=%~1
) ELSE (
	SET SLACK_INDEX=%~1
)
SHIFT
GOTO parse
:endparse


:: If the user-provided "index.js" is not found, try to find it

IF NOT "%SLACK_INDEX%" == "" IF NOT EXIST "%SLACK_INDEX%" (
	IF EXIST "%SLACK_INDEX%AppData\Local\slack\app-2.5.1\resources\app.asar.unpacked\src\static\index.js" (
		SET SLACK_INDEX=%SLACK_INDEX%AppData\Local\slack\app-2.5.1\resources\app.asar.unpacked\src\static\index.js
	) ELSE IF EXIST "%SLACK_INDEX%\AppData\Local\slack\app-2.5.1\resources\app.asar.unpacked\src\static\index.js" (
		SET SLACK_INDEX=%SLACK_INDEX%\AppData\Local\slack\app-2.5.1\resources\app.asar.unpacked\src\static\index.js
	) ELSE IF EXIST "%SLACK_INDEX%app-2.5.1\resources\app.asar.unpacked\src\static\index.js" (
		SET SLACK_INDEX=%SLACK_INDEX%app-2.5.1\resources\app.asar.unpacked\src\static\index.js
	) ELSE IF EXIST "%SLACK_INDEX%\app-2.5.1\resources\app.asar.unpacked\src\static\index.js" (
		SET SLACK_INDEX=%SLACK_INDEX%\app-2.5.1\resources\app.asar.unpacked\src\static\index.js
	)
)


:: Try to find slack if not provided by user

IF "%SLACK_INDEX%" == "" (
	FOR /F %%t IN ('DIR /B /ON %UserProfile%\AppData\Local\slack\app-?.*.*') DO (
		SET SLACK_INDEX=%UserProfile%\AppData\Local\slack\%%t\resources\app.asar.unpacked\src\static\index.js
	)
)


:: Check so "index.js" exists

IF "%SLACK_INDEX%" == "" (
	ECHO Cannot find Slack's index file.
	PAUSE & EXIT /B 1
)

IF NOT EXIST "%SLACK_INDEX%" (
	ECHO Cannot find Slack's index file: %SLACK_INDEX%
	PAUSE & EXIT /B 1
)


:: Does backup exists? If so, do update

IF EXIST "%SLACK_INDEX%.mwsbak" (
	COPY /Y "%SLACK_INDEX%.mwsbak" "%SLACK_INDEX%" >NUL
)


:: Check so "index.js" is known to work with the script

FOR /F "skip=1 delims=" %%L IN ('CertUtil -hashfile %SLACK_INDEX%') DO SET "INDEX_HASH=%%L" & GOTO breakhashloop
:breakhashloop

IF "%FORCE%" == "" IF NOT "%INDEX_HASH%" == "f07fabb32b109500fb264083b8685a85197df522" (
	ECHO Unrecognized index file: %SLACK_INDEX%
	ECHO Call with '-f' flag to suppress this check.
	PAUSE & EXIT /B 1
)


:: Ensure "index.js" contains "startup();"

FINDSTR /R /C:"^    startup();" "%SLACK_INDEX%" >NUL
IF %ERRORLEVEL% NEQ 0 (
	ECHO Cannot find 'startup(^);' in index file: %SLACK_INDEX%
	PAUSE & EXIT /B 1
)


:: Does backup exists? If not, make one

IF NOT EXIST "%SLACK_INDEX%.mwsbak" (
	COPY "%SLACK_INDEX%" "%SLACK_INDEX%.mwsbak" >NUL
)


:: Write code for MathJax injection

DEL "%SLACK_INDEX%"
IF EXIST "%SLACK_INDEX%" (
	ECHO Cannot write to Slack's index file: %SLACK_INDEX%
	PAUSE & EXIT /B 1
)

FOR /F "delims=" %%L IN (%SLACK_INDEX%.mwsbak) DO (
	IF "%%L" == "    startup();" (
		>>"%SLACK_INDEX%" (
			ECHO.    startup(^);
			ECHO.
			ECHO.    // *** Code injected for MathJax support
			ECHO.    // See: https://github.com/fsavje/math-with-slack
			ECHO.
			ECHO.    var mathjax_inject_script = `
			ECHO.      var mathjax_config = document.createElement("script"^);
			ECHO.      mathjax_config.type = "text/x-mathjax-config";
			ECHO.      mathjax_config.text = \`
			ECHO.        MathJax.Hub.Config({
			ECHO.          messageStyle: "none",
			ECHO.          extensions: ["tex2jax.js"],
			ECHO.          jax: ["input/TeX", "output/HTML-CSS"],
			ECHO.          tex2jax: {
			ECHO.            skipTags: ["script","noscript","style","textarea","pre","code"],
			ECHO.            ignoreClass: "ql-editor",
			ECHO.            inlineMath: [ ['\$','\$'] ],
			ECHO.            displayMath: [ ['\$\$','\$\$'] ],
			ECHO.            processEscapes: true
			ECHO.          },
			ECHO.          TeX: {
			ECHO.            extensions: ["AMSmath.js", "AMSsymbols.js", "noErrors.js", "noUndefined.js"]
			ECHO.          }
			ECHO.        }^);
			ECHO.        \`;
			ECHO.      var mathjax_script = document.createElement("script"^);
			ECHO.      mathjax_script.type = "text/javascript";
			ECHO.      mathjax_script.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.0/MathJax.js";
			ECHO.      document.getElementsByTagName("head"^)[0].appendChild(mathjax_config^);
			ECHO.      document.getElementsByTagName("head"^)[0].appendChild(mathjax_script^);
			ECHO.
			ECHO.      var render = function (records, observer^) {
			ECHO.          MathJax.Hub.Queue(["Typeset", MathJax.Hub]^);
			ECHO.      };
			ECHO.      var target = document.querySelector('#msgs_div'^);
			ECHO.      var observer = new MutationObserver(render^);
			ECHO.      var config = { attributes: false, childList: true, characterData: true, subtree: true };
			ECHO.      observer.observe(target, config^);
			ECHO.    `;
			ECHO.
			ECHO.    window.webviews = document.querySelectorAll(".TeamView webview"^);
			ECHO.    setTimeout(function(^) {
			ECHO.      for(var i = 0; i ^< webviews.length; i++^) {
			ECHO.        webviews[i].executeJavaScript(mathjax_inject_script^);
			ECHO.      }
			ECHO.    }, 20000^);
			ECHO.
			ECHO.    // *** End injected MathJax
			ECHO.
		)
	) ELSE (
		>>"%SLACK_INDEX%" ECHO.%%L
	)
)

ECHO MathJax successfully injected into Slack. Please restart Slack client.
PAUSE
