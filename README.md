![CI](https://github.com/thisiscam/math-with-slack/workflows/CI/badge.svg)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-3.6.json)
![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/macOS-3.6.json)
![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/windows-3.6.json)
<details>
<summary>
Expand to see all tested systems
</summary>
<p>

# All environments on latest Slack app (updated nightly)

Environments below with passing badges are tested to work -- that the install scripts completes succesfully.  
However, if you find that something is not working (e.g. math rendering does not appear), please file an [issue](../../issues) with your environment! 

### Ubuntu

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-2.7.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-3.6.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-3.7.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-3.8.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-pypy2.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/ubuntu-pypy3.json)


### MacOS

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/macOS-2.7.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/macOS-3.6.json)


### Windows

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/windows-2.7.json)

![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/thisiscam/02c2a5208be4374a6d0eab50ebb8e021/raw/windows-3.6.json)

</p>
</details>


# Rendered math (MathJax) with Slack's desktop client

[Slack](https://slack.com) does not display rendered math. The `math-with-slack` script allows you to write nice-looking math using familiar TeX syntax by injecting [MathJax](https://www.mathjax.org) into Slack's desktop client. This approach has several advantages over the plugin/bot solution:

  * You can write both inline- and display-style equations.
  * You can edit equations after you've posted them.
  * Nothing is sent to external servers for rendering.

The downside is that equations are not rendered for team members without the MathJax injection.


![Math Slack Example](math-slack.gif "Amazing maths!")


## How do I install it?

Get and run the script. Restart the Slack client. You're done!

Windows users without Python installed can skip and jump to [binary release](#beta-binary-release-for-windows).

### Getting the script

#### Option 1: Raw script content

There are many ways to get the script. 
This [link to math-with-slack.py](math-with-slack.py/?raw=True) should take you to the raw file content of the script, with the version relative same as README.md that you are looking at (i.e. on the same commit).
From there you can simply save the file's content to a local file `math-with-slack.py` (e.g. you can copy the entire content, and use your favorite editor to save the content) --- this process should be the same for all platforms, and works as long as you have a decent browser and working editor.


#### Option 2: using a download tool (e.g. curl, wget) 

1. Copy the URL of [link to math-with-slack.py](math-with-slack.py/?raw=True) (e.g. right click on the link -> copy URL).

2. Assuming on Mac and/or Linux, use one of the alternatives:
  - With the tool `curl` available. Run the following in a terminal:
  ```shell
  curl -L {PASTE_THE_COPIED_LINK_HERE} > math-with-slack.py
  ```
  - With the tool `wget` available. Run the following in a terminal:
  ```
  wget {PASTE_THE_COPIED_LINK_HERE} -O math-with-slack.py
  ```

#### Option 3: using git

With `git` available, you can also clone this repo, and access the script `math-with-slack.py` directly!


### Running the script

- MacOS and Linux

 ```shell
 cd path/to/math-with-slack
 sudo python math-with-slack.py 
 ```
 The installation should take effect after restarting Slack.
 
- Windows
 You need to exit your Slack before the installation.
 ```shell
 cd path\to\math-with-slack
 python math-with-slack.py
 ```

### Beta Binary Release for Windows

We have also included pre-built executables for Windows in case Python is not available. Please see our [Releases page](../../releases) for more details.

### Selecting a Slack version

If multiple versions of Slack are found on your computer, you will be asked to select one from them.
   
   ```
   python math-with-slack.py
   Several verisons of Slack were installed.
    0: /mnt/c/Users/***/AppData/Local/slack/app-4.9.0/resources/app.asar (default)
    1: /mnt/c/Users/***/AppData/Local/slack/app-4.8.0/resources/app.asar
   Please select a version (#/Stop): 1
   ```
   
   You can either enter the number indicating one of the listed versions
   or type Enter to select the first one.
   
   **Currently, we only support Slack installed from [Slack installer](https://slack.com/downloads/windows).
   If your Slack is installed through Microsoft Store, `math-with-slack` is not able to modifiy files in `WindowsApps`
   folder hence not able to embedded our script.**


### Package and software managers

The script needs write permissions in the Slack directory in order to inject the MathJax code. 
Some package and software managers write protect their directories, and `math-with-slack` cannot be installed 
if Slack is installed through such a manager. This is the case for both the Windows Store and Snap versions of Slack. 
You should use the version downloaded from [Slack's website](https://slack.com/downloads/windows) if you want to use 
`math-with-slack`. The script should, however, work with most package managers if 
[you manage to grant the script write permission](https://github.com/fsavje/math-with-slack/issues/32#issuecomment-479852799).


### MathJax versions and URLs

The default MathJax is of version 3.1.0 and downloaded from `https://registry.npmjs.org/mathjax/-/mathjax-3.1.0.tgz`, which is a registry of npmjs. 

The script also works with other versions of MathJax 3 and we list a table
of versions that we have tested and the corresponding URLs.

| Version | URLs                                                                                                         | File Size |
|---------|--------------------------------------------------------------------------------------------------------------|-----------|
| 3.1.0   | https://registry.npmjs.org/mathjax/-/mathjax-3.1.0.tgz <br> https://r.cnpmjs.org/mathjax/-/mathjax-3.1.0.tgz | 4.5 MB    |
| 3.0.5   | https://registry.npmjs.org/mathjax/-/mathjax-3.0.5.tgz <br> https://r.cnpmjs.org/mathjax/-/mathjax-3.0.5.tgz | 4.4 MB    |
| 3.0.4   | https://registry.npmjs.org/mathjax/-/mathjax-3.0.4.tgz <br> https://r.cnpmjs.org/mathjax/-/mathjax-3.0.4.tgz | 4.4 MB    |
| 3.0.1   | https://registry.npmjs.org/mathjax/-/mathjax-3.0.1.tgz <br> https://r.cnpmjs.org/mathjax/-/mathjax-3.0.1.tgz | 6.3 MB    |
| 3.0.0   | https://registry.npmjs.org/mathjax/-/mathjax-3.0.0.tgz <br> https://r.cnpmjs.org/mathjax/-/mathjax-3.0.0.tgz | 6.3 MB    |


Some URLs works better for certain areas. You can use any URL in the
table to install `math-with-slack`.

   ```shell
   cd path\to\math-with-slack
   python math-with-slack.py --mathjax-url=https://r.cnpmjs.org/mathjax/-/mathjax-3.0.5.tgz
   ```


### Uninstall

To uninstall, run the script again with the `-u` flag:

```shell
python math-with-slack.py -u
```


### Updating Slack

The code injected by the script might be overwritten when you update the Slack app. 
If your client stops rendering math after an update, re-run the script as above and it should work again.


### If Slack cannot be found

If you've installed Slack in some exotic place, the script might not find the installation by itself or it 
might find the wrong installation. In such cases, you need to specify the location of Slack's
`app.asar` file as a parameter:

```shell
python math-with-slack.py --app-file=/My_Apps/Slack.app/Contents/Resources/app.asar
```

```shell
python math-with-slack.py --app-file=c:/Users/yourusername/AppData/Local/slack/app-4.7.0/resources/app.asar
```


## How do I get my math rendered?

As you do in TeX, use `$ ... $` for inline math and `$$ ... $$` for display-style math. 
If you need to write a lot of dollar-signs in a message and want to prevent rendering,
use backslash to escape them: `\$`.

Note that only users with MathJax injected in their client will see the rendered version of your math.
Users with the standard client will see the equations just as you wrote them 
(i.e., unrendered including the dollar signs).

### TeX Customization

The script allows one to customize MathJax at installation time. 
Currently the script allows the user to supply an optional [TeX input processor option](http://docs.mathjax.org/en/latest/options/input/tex.html) to customize the MathJax rendering. 
For example, to instead use `\( ... \)` for inline math and `\[ ... \]` for display-style math, and enable the package [physics](http://docs.mathjax.org/en/latest/input/tex/extensions/physics.html?highlight=physics) support, one may use the following command line arguments during installation:
```shell
python math-with-slack.py --mathjax-tex-options="{\
  packages: {'[+]': ['noerrors', 'noundefined', 'physics']}, \
  inlineMath: [['\\\(', '\\\\)']], \
  displayMath: [['\\\\[', '\\\\]']], \
}"
```
Note that a common scenario is when a team of people uses this plugin. In this case it will be desirable to share the same configuration for all the members. 

## How does it work?

The script alters how Slack is loaded. Under the hood, the desktop client is based on ordinary web technology. 
The modified client loads the [MathJax library](https://www.mathjax.org) after start-up and adds a listener for messages.
As soon as it detects a new message, it looks for TeX-styled math and tries to render.
Everything is done in the client. Messages are *never* sent to servers for rendering.


## Can I contribute?

Yes, please. Just add an [issue](../../issues) or a [pull request](../../pulls).


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
* [thisiscam](https://github.com/thisiscam)
* [YingzhouLi](https://github.com/YingzhouLi)

**Inspiration**

This [comment](https://gist.github.com/DrewML/0acd2e389492e7d9d6be63386d75dd99#gistcomment-1981178) by [jouni](https://github.com/jouni) was extremely helpful. So was this [snippet](https://gist.github.com/etihwnad/bc63ec9b87af586e1435) by [etihwnad](https://github.com/etihwnad).
