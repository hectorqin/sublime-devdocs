Sublime-devdocs
===========================
****
### Author:hector
### E-mail:hectorqin@163.com
****

Quick search symbol in devdocs offline plugin for Sublime Text 3


### Installation

The easiest way to install is using [Package Control][pc], where [Sublime-devdocs][theme] is listed as **`Devdocs offline`**.

1. Open `Command Palette` using menu item `Tools → Command Palette...`

2. Choose `Package Control: Install Package`

3. Find `Devdocs offline` and hit `Enter`

Or install it by downloading the zip, extract it and put it into the package dir of sublime, rename it to "Devdocs offline", and then it may work fine!

***

### How to use

1. Open `Command Palette` using menu item `Tools → Command Palette...`

2. Choose `Devdocs: All Languages`

3. Search what language you need and hit `Enter`. It will download the language docs from [devdocs.io][devdocs.io]

4. After download, you can use the commands the following

***

### Commands

1. `Devdocs: All Languages`  Show all supported language with version in the panel, and choose language to install or uninstall

2. `Devdocs: Show Definition`  Search the definition of your selected symbol in the syntax matched language. If found, it will be displayed in the popup

3. `Devdocs: Search Symbol`  Search symbol in a quick panel, choose item to show the definition of symbol

4. `Devdocs: Set Default Version`  Set the syntax matched language default search version when the language has many versions

5. `Devdocs: Set Syntax Alias`  Set the syntax matched to which language, it's useful when the plugin can't identify the language of the syntax

***

### Settings

1. Default Settings

    ```js
    {
        // This file is default setting of this plugin, please don't edit this file

        // Download proxy
        "http_proxy": "",

        // Max height and width of popup
        "popup_max_height": 1080,
        "popup_max_width": 1280,

        // Set true to use style file to set custom styles, this is experimental
        "use_style": false,

        // Default language version for symbol search
        "language_default_version": {

        },
        // Usually, this plugin parse the language type from the syntax setting of the view, this may be not accurate, you can set this configuration to set the syntax alias
        "syntax_alias":{

        }
    }
    ```

2. If you want to modify the setting, please use menu item `Preferences → Package Settings → Devdocs offline → Settings – User`

***

### keys

    ```js
    [
        { "keys": ["ctrl+alt+d"], "command": "devdocs_show_definition"},
        { "keys": ["ctrl+alt+s"], "command": "devdocs_search_symbol"},
    ]
    ```

### License

[Apache](all/COPYING)

<!-- Links -->

[pc]: https://packagecontrol.io/
[devdocs.io]: https://devdocs.io "devdocs.io"
[theme]: https://packagecontrol.io/packages/DevDocs%20offline

