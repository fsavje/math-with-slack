# LaTeX Math (MathJax) with Slack's desktop client

[Slack](https://slack.com) does not support math. This shell script injects [MathJax](https://www.mathjax.org) into Slack's desktop client. This allows you to write both inline- and display-style math. You can also edit equations after you've posted them.

![Math Slack Example](math-slack.gif "Amazing maths!")


## How do I install it?

The script has only been tested on macOS, but should work on Linux systems as well. (And, with some effort, probably on Windows as well.)

Assuming that Slack is installed at the expected place (i.e., `/Applications/Slack.app`), simply download [math_with_slack.sh](math_with_slack.sh) and run:

```shell
./math_with_slack.sh
```

After restarting the Slack client, you're all done!

If you've installed Slack at some exotic place, or you're running Linux, you need to specify the location of Slack's `index.js` file as the first parameter. For example:

```shell
./math_with_slack.sh /Applications/Slack.app/Contents/Resources/app.asar.unpacked/src/static/index.js
```


## How do I get my math rendered?

As with TeX, simply use `$ ... $` for inline math and `$$ ... $$` for display-style math. If you need to write a lot dollar-signs in a message and want to prevent rendering, use backslash to escape them: `\$`. 

It is worth noting that only users with MathJax injected in their client will see the rendered version of your math. Users with the standard client will see the equations just as you wrote them.

## How does it work?

The script alters how Slack is loaded. Under the hood, the desktop client is based on ordinary web technology. After startup, the modified client loads the [MathJax library](https://www.mathjax.org) and adds a listener for messages. As soon as it detects a new message, it looks for TeX-styled math and tries to render it. Everything is done completely in the client; messages are *never* sent to any server for rendering.


## Can I contribute?

Yes, please. Go ahead and file an [issue](https://github.com/fsavje/math-with-slack/issues) or a [pull request](https://github.com/fsavje/math-with-slack/pulls).


## References and inspiration

This [comment](https://gist.github.com/DrewML/0acd2e389492e7d9d6be63386d75dd99#gistcomment-1981178) by [jouni](https://github.com/jouni) was extremely helpful. So was this [snippet](https://gist.github.com/etihwnad/bc63ec9b87af586e1435) by [etihwnad](https://github.com/etihwnad).
