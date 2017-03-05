# Rendered math (MathJax) with Slack's desktop client

[Slack](https://slack.com) does not display rendered math. This script injects [MathJax](https://www.mathjax.org) into Slack's desktop client, which allows you to write both nice-looking inline- and display-style math. You can also edit equations after you've posted them.

![Math Slack Example](math-slack.gif "Amazing maths!")


## How do I install it?

On macOS and Linux systems, simply download and run the script with:

```shell
curl -O https://raw.githubusercontent.com/fsavje/math-with-slack/master/math_with_slack.sh && chmod +x math_with_slack.sh
./math_with_slack.sh
```

After restarting the Slack client, you're all done!

If you've installed Slack in some exotic place, you might need to specify its location. For example:

```shell
./math_with_slack.sh /My_Applications/Slack.app
```

The script does not yet run on Windows.


## How do I get my math rendered?

As with TeX, use `$ ... $` for inline math and `$$ ... $$` for display-style math. If you need to write a lot of dollar-signs in a message and want to prevent rendering, use backslash to escape them: `\$`. 

Note that only users with MathJax injected in their client will see the rendered version of your math. Users with the standard client will see the equations just as you wrote them.

## How does it work?

The script alters how Slack is loaded. Under the hood, the desktop client is based on ordinary web technology. The modified client loads the [MathJax library](https://www.mathjax.org) after start-up and adds a listener for messages. As soon as it detects a new message, it looks for TeX-styled math and tries to render. Everything is done completely in the client; messages are *never* sent to any server for rendering.


## Can I contribute?

Yes, please. Go ahead and file an [issue](https://github.com/fsavje/math-with-slack/issues) or a [pull request](https://github.com/fsavje/math-with-slack/pulls).


## References and inspiration

This [comment](https://gist.github.com/DrewML/0acd2e389492e7d9d6be63386d75dd99#gistcomment-1981178) by [jouni](https://github.com/jouni) was extremely helpful. So was this [snippet](https://gist.github.com/etihwnad/bc63ec9b87af586e1435) by [etihwnad](https://github.com/etihwnad).
