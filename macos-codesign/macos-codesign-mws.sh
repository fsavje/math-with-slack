SLACK_APP_PATH=/Applications/Slack.app/
SLACK_ENTITLEMENTS_XML=$(mktemp -t slack-entitlements)

codesign -d --entitlements $SLACK_ENTITLEMENTS_XML $SLACK_APP_PATH
codesign --entitlements $SLACK_ENTITLEMENTS_XML --force --sign math-with-slack-codesign $SLACK_APP_PATH
