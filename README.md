# Rendered math (MathJax) with Slack's desktop client

[Slack](https://slack.com) does not display rendered math. The `math-with-slack` script allows you to write nice-looking math using familiar TeX syntax by injecting [MathJax](https://www.mathjax.org) into Slack's desktop client. This approach has several advantages over the plugin/bot solution:

  * You can write both inline- and display-style equations.
  * You can edit equations after you've posted them.
  * Nothing is sent to external servers for rendering.

The downside is that equations are not rendered for team members without the MathJax injection.


![Math Slack Example](math-slack.gif "Amazing maths!")


## How do I install it?

Get and run the script. Restart the Slack client. You're done!

### Getting the script

### Mac and Linux

Run the following in a terminal:

```shell
curl -OL https://raw.githubusercontent.com/psg-mit/math-with-slack/master/math-with-slack.py
sudo python math-with-slack.py
```

### Windows

!!! Current support for windows is unknown

[Download the script](https://github.com/fsavje/math-with-slack/releases/download/v0.2.5/math-with-slack.bat) and double-click to run. Alternatively, run it in the command prompt with:

```shell
math-with-slack.bat
```

(Windows will probably give you a security warning since the script is downloaded from Internet.)


### Package and software managers

The script needs write permissions in the Slack directory in order to inject the MathJax code. Some package and software managers write protect their directories, and `math-with-slack` cannot be installed if Slack is installed through such a manager. This is the case for both the Windows Store and Snap versions of Slack. You should use the version downloaded from [Slack's website](https://slack.com/downloads/windows) if you want to use `math-with-slack`. The script should, however, work with most package managers if [you manage to grant the script write permission](https://github.com/fsavje/math-with-slack/issues/32#issuecomment-479852799).


### Uninstall

To uninstall, run the script again with the `-u` flag:

```shell
sudo bash math-with-slack.sh -u
```

```shell
math-with-slack.bat -u
```


### Updating Slack

The code injected by the script might be overwritten when you update the Slack app. If your client stops rendering math after an update, re-run the script as above and it should work again.


### If Slack cannot be found

If you've installed Slack in some exotic place, the script might not find the installation by itself or it might find the wrong installation. In such cases, you need to specify the location of Slack's `app.asar.unpacked/src/static` folder as a parameter:

```shell
sudo bash math-with-slack.sh /My_Apps/Slack.app/Contents/Resources/app.asar.unpacked/src/static
```

```shell
math-with-slack.bat E:\My_Apps\slack\app-2.5.1\resources\app.asar.unpacked\src\static
```


## How do I get my math rendered?

As you do in TeX, use `$ ... $` for inline math and `$$ ... $$` for display-style math. If you need to write a lot of dollar-signs in a message and want to prevent rendering, use backslash to escape them: `\$`.

Note that only users with MathJax injected in their client will see the rendered version of your math. Users with the standard client will see the equations just as you wrote them (i.e., unrendered including the dollar signs).


## How does it work?

The script alters how Slack is loaded. Under the hood, the desktop client is based on ordinary web technology. The modified client loads the [MathJax library](https://www.mathjax.org) after start-up and adds a listener for messages. As soon as it detects a new message, it looks for TeX-styled math and tries to render. Everything is done in the client. Messages are *never* sent to servers for rendering.


## Can I contribute?

Yes, please. Just add an [issue](https://github.com/fsavje/math-with-slack/issues) or a [pull request](https://github.com/fsavje/math-with-slack/pulls).


**Thanks to past contributors:**

* [Caster](https://github.com/Caster)
* [chrispanag](https://github.com/chrispanag)
* [crstnbr](https://github.com/crstnbr)
* [gauss256](https://github.com/gauss256)
* [jeanluct](https://github.com/jeanluct)
* [LaurentHayez](https://github.com/LaurentHayez)
* [NKudryavka](https://github.com/NKudryavka)
* [peroxyacyl](https://github.com/peroxyacyl)
* [Spenhouet](https://github.com/Spenhouet)
* [Xyene](https://github.com/Xyene)


**Inspiration**

This [comment](https://gist.github.com/DrewML/0acd2e389492e7d9d6be63386d75dd99#gistcomment-1981178) by [jouni](https://github.com/jouni) was extremely helpful. So was this [snippet](https://gist.github.com/etihwnad/bc63ec9b87af586e1435) by [etihwnad](https://github.com/etihwnad).
