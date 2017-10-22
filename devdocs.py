import sublime
import sublime_plugin

import re
import os
import shutil
import tarfile
import webbrowser
import time
import urllib
from Default import symbol as sublime_symbol
from html.parser import HTMLParser

package_name = "Devdocs"
setting_file = package_name + '.sublime-settings'
entities = {
    "iso": False,
    "html": False
}
language_alias = {
    "jquery_core": "jquery"
}
all_languages = None
all_languages_display = None
installed_languages = None
languages_index = {}

installed_tip = {
    'toggle': 'Installed, click to uninstall',
    'set_as_default': 'Installed, click to set as default version'
}
uninstalled_tip = {
    'toggle': 'Uninstalled, click to install',
    'set_as_default': 'Uninstalled, click to install and set as default version'
}

currentSettings = None
popup_default_max_width = 800
popup_default_max_height = 300


def plugin_loaded():
    global currentSettings, setting_file
    currentSettings = sublime.load_settings(setting_file)
    docs_path = getDocsPath(True)
    if not os.path.isdir(docs_path):
        os.makedirs(docs_path)

    if not callable(sublime_symbol.symbol_at_point) or not callable(sublime_symbol.navigate_to_symbol):
        sublime.error_message(
            'Cannot find symbol_at_point from Default.sublime-package\n\nPlease restore the file which usually replaced by outdated localizations')


def getSetting(key, default=None):
    global currentSettings
    return currentSettings.get(key, default)


def setSetting(key, value):
    global currentSettings, setting_file
    currentSettings.set(key, value)
    sublime.save_settings(setting_file)


def getAllLanguages():
    global all_languages
    if all_languages == None:
        all_languages = sublime.decode_value(
            sublime.load_resource(getPackagePath() + '/languages.json'))
    return all_languages


def checkAllLanguagesForDisplay(update=False, tipType='toggle'):
    global all_languages_display
    if all_languages_display == None:
        all_languages_display = []
        languages = getAllLanguages()
        for key, language in enumerate(languages):
            all_languages_display.append([language, uninstalled_tip[tipType]])

    installed_lgs = getAllInstalledLanguages(update)
    for key, language in enumerate(all_languages_display):
        if installed_lgs.get(parseLanguageName(language[0])) != None:
            all_languages_display[key][1] = installed_tip[tipType]

    return all_languages_display


def getAllInstalledLanguages(update=False):
    global installed_languages
    changed = False
    if installed_languages == None or update:
        if os.path.isfile(getDocsPath(True) + '/docs.json'):
            installed_languages = sublime.decode_value(
                sublime.load_resource(getDocsPath() + '/docs.json'))
        else:
            installed_languages = {}
            changed = True
        for _key in list(installed_languages):
            language = installed_languages[_key]
            if not os.path.isfile(getLanguagePath(language["slug"], True) + '/index.json'):
                installed_languages.pop(_key)
                changed = True
                if languages_index.get(_key) != None:
                    languages_index.pop(_key)
    if changed:
        saveInstalledLanguages()
    return installed_languages


def saveInstalledLanguages():
    global installed_languages
    with open(getDocsPath(True) + '/docs.json', 'w') as f:
        f.write(sublime.encode_value(installed_languages, True))


def isInstalled(language, update=False):
    installed_lgs = getAllInstalledLanguages(update)
    if installed_lgs.get(parseLanguageName(language)) != None:
        return True
    else:
        return False


def setSyntaxAlias(syntax, alias):
    syntax_alias = getSetting('syntax_alias', {})
    syntax_alias[syntax] = alias
    setSetting('syntax_alias', syntax_alias)


def getSyntaxAlias(syntax):
    syntax_alias = getSetting('syntax_alias', {})
    if syntax_alias.get(syntax):
        return syntax_alias.get(syntax)
    else:
        return False


def setLanguageDefaultVersion(language, version):
    language_default_version = getSetting('language_default_version', {})
    language_default_version[language] = version
    setSetting('language_default_version', language_default_version)


def getLanguageDefaultVersion(language):
    language_default_version = getSetting('language_default_version', {})
    if language_default_version.get(language):
        return language_default_version.get(language)
    else:
        return language


def searchInAllLanguages(name, tipType='toggle'):
    languages = getAllLanguages()
    search_languages_display = []
    for key, language in enumerate(languages):
        if name in language:
            if isInstalled(language):
                search_languages_display.append(
                    [language, installed_tip[tipType]])
            else:
                search_languages_display.append(
                    [language, uninstalled_tip[tipType]])
    return search_languages_display


def getPackagePath(absolute=False):
    if not absolute:
        return 'Packages' + '/' + package_name
    else:
        return sublime.packages_path() + '/' + package_name


def getDocsPath(absolute=False):
    return getPackagePath(absolute) + '/docs'


def getLanguagePath(language, absolute=False):
    return getDocsPath(absolute) + '/' + language


def parseLanguageName(language, forPath=False):
    global language_alias
    if language_alias.get(language):
        return language_alias.get(language)
    if language[-1] == '@':
        language = language[:-1]
    if forPath:
        return language.replace('@', '~')
    else:
        return language


def parseViewLanguage(view):
    syntax = view.settings().get('syntax')
    print("Now view syntax " + syntax)
    alias = getSyntaxAlias(syntax)
    if alias:
        print("Found view syntax alias " + alias)
        return getLanguageDefaultVersion(alias), alias
    matchObj = re.search(r'([^\/]*)\.', syntax)
    if matchObj:
        language = matchObj.group(1).lower()
    else:
        language = "php"
    return getLanguageDefaultVersion(language), language


def getLanguageIndex(language):
    global languages_index
    if not languages_index.get(language):
        index_json = sublime.decode_value(
            sublime.load_resource(getLanguagePath(language) + '/index.json'))
        languages_index[language] = index_json["entries"]
    return languages_index[language]


def getAllSymbol(language):
    language = parseLanguageName(language, True)
    indexArr = getLanguageIndex(language)
    print(indexArr)
    allSymbol = []
    for key, _symbol in enumerate(indexArr):
        allSymbol.append(_symbol['name'])
    return allSymbol


def getSymbolInIndex(symbol, language):
    language = parseLanguageName(language, True)
    indexArr = getLanguageIndex(language)
    for key, _symbol in enumerate(indexArr):
        if symbol == _symbol['name']:
            return _symbol
        if symbol + '()' == _symbol['name']:
            return _symbol
    return None


def getSymbolDescriptionFromHtml(path, language):
    language = parseLanguageName(language, True)
    pathinfo = path.split('#')
    html_path = getLanguagePath(language) + '/' + pathinfo[0] + '.html'
    print("Load From " + html_path)
    output = sublime.load_resource(html_path)
    dic = {
        '&mdash;': chr(8212),
        '&quot;': '"',
        '<br>': '',
        '&#039;': "'",
        '&$': "&amp;$",
        '&raquo;': chr(187),
    }
    pattern = "|".join(map(re.escape, dic.keys()))

    output = re.sub(pattern, lambda m: dic[m.group()], output)
    return output


def decodeEntity(xml, category='iso'):
    global entities
    if not isinstance(xml, str):
        return xml
    if entities[category]:
        forward, reverse = entities[category]
    else:
        resourceMap = {
            "iso": "IsoEntities.json",
            "html": "HtmlEntities.json",
        }
        forward = sublime.decode_value(sublime.load_resource(
            getPackagePath() + '/' + resourceMap[category]))

        reverse = dict((v, k) for k, v in forward.items())
        entities[category] = (forward, reverse)

    def parseEntity(match):
        entity = match.group(1)
        try:
            if entity.isdigit():
                return reverse[int(entity)]
            else:
                return chr(forward[entity])
        except:
            return match.group(0)
    xml = re.sub('&([a-zA-Z0-9]+);', parseEntity, xml)
    return xml


def extract(tar_path, target_path, mode='r:gz'):
    try:
        tar = tarfile.open(tar_path, mode)
        tar.extractall(target_path)
        tar.close()
        return True
    except Exception as e:
        print('Extract fail ' + e.__class__.__name__)
        return False


def uninstallLanguage(languageWithVersion):
    languageForPath = parseLanguageName(languageWithVersion, True)
    print('Uninstall languageWithVersion ' + languageWithVersion)
    language_path = getDocsPath(True) + "/" + languageForPath
    if os.path.isdir(language_path):
        shutil.rmtree(language_path)
    if installed_languages.get(languageWithVersion) != None:
        installed_languages.pop(languageWithVersion)
    if languages_index.get(languageWithVersion) != None:
        languages_index.pop(languageWithVersion)
    saveInstalledLanguages()


def installLanguage(languageWithVersion):
    if not languageWithVersion:
        return False

    uninstallLanguage(languageWithVersion)

    languageWithVersion = parseLanguageName(languageWithVersion)
    print('Install languageWithVersion ' + languageWithVersion)

    languageForPath = languageWithVersion.replace('@', '~')
    err = None
    try:
        url = 'http://dl.devdocs.io/' + languageForPath + '.tar.gz'
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
        print('Downloading ' + url)
        req = urllib.request.Request(url)
        req.add_header('User-Agent', user_agent)

        filename = getDocsPath(True) + '/' + \
            languageForPath + '.tar.gz.downloading'
        http_proxy = getSetting('http_proxy')
        if http_proxy:
            proxy_handler = urllib.request.ProxyHandler({'http': http_proxy})
            # proxy_auth_handler = urllib.request.ProxyBasicAuthHandler()
            # proxy_auth_handler.add_password('realm', 'host', 'username', 'password')

            opener = urllib.request.build_opener(proxy_handler)
            response = opener.open(req)
        else:
            response = urllib.request.urlopen(req)
        try:
            # assume correct header
            totalsize = int(response.headers['Content-Length'])
        except NameError:
            totalsize = None
        except KeyError:
            totalsize = None

        outputfile = open(filename, 'wb')

        readsofar = 0
        chunksize = 8192
        try:
            while(True):
                # download chunk
                data = response.read(chunksize)
                if not data:  # finished downloading
                    break
                readsofar += len(data)
                outputfile.write(data)  # save to filename
                if totalsize:
                    # report progress
                    percent = readsofar * 1e2 / totalsize  # assume totalsize > 0
                    sublime.status_message(
                        package_name + ': %.0f%% downloading %s' % (percent, languageForPath,))
                else:
                    kb = readsofar / 1024
                    sublime.status_message(
                        package_name + ': %.0f KB downloading %s' % (kb, languageForPath,))
        finally:
            outputfile.close()
            if totalsize and readsofar != totalsize:
                os.unlink(filename)
                err = 'Download failed'

    except (urllib.error.HTTPError) as e:
        err = '%s: HTTP error %s contacting API' % (__name__, str(e.code))
    except (urllib.error.URLError) as e:
        err = '%s: URL error %s contacting API' % (__name__, str(e.reason))
    except Exception as e:
        err = e.__class__.__name__

    print("Download success")

    if not err:
        newname = getDocsPath(True) + '/' + languageForPath + '.tar.gz'
        if os.path.isfile(newname):
            os.unlink(newname)
        os.rename(filename, newname)
        print("Extract " + newname)
        if extract(newname, getDocsPath(True) + '/' + languageForPath):
            global installed_languages
            installed_languages[languageWithVersion] = {
                "mtime": time.time(),
                "name": languageWithVersion,
                "slug": languageForPath
            }
            os.unlink(newname)
            saveInstalledLanguages()
            return True
        else:
            err = 'Extract file error'

    print(err)
    sublime.message_dialog('LanguageVersion ' + languageWithVersion +
                           ' install failed. Please try again.')
    return False


class DevdocsShowDefinitionCommand(sublime_plugin.TextCommand):
    match_languages = None

    def want_event(self):
        return True

    def run(self, edit, event=None, symbol=None):
        language, language_type = parseViewLanguage(self.view)
        print("Current view language:" + language)
        if not isInstalled(language, True):
            self.view.run_command("devdocs_set_default_version")
            return False
        if symbol == None:
            if event:
                pt = self.view.window_to_text((event["x"], event["y"]))
            else:
                pt = self.view.sel()[0]
            symbol, locations = sublime_symbol.symbol_at_point(
                self.view, pt)
        print("Looking for symbol " + symbol + " in " + language)
        symbolInfo = getSymbolInIndex(symbol, language)
        if not symbolInfo:
            print("Not found the symbol " + symbol)
            return
        print("Found symbol")
        print(symbolInfo)
        self.show_popup(
            symbol, getSymbolDescriptionFromHtml(symbolInfo['path'], language))

    def show_popup(self, symbol, symbolDescription):
        global popup_default_max_height, popup_default_max_width
        output = symbolDescription

        # if getSetting('debug'):
        #     print(output)

        width, height = self.view.viewport_extent()
        output = self.formatPopup(output, symbol=symbol)

        # It seems sublime will core when the output is too long
        # In some cases the value can set to 76200, but we use a 65535 for
        # safety.
        output = output[:65535]

        self.view.show_popup(
            output,
            # flags=sublime.COOPERATE_WITH_AUTO_COMPLETE | sublime.HTML,
            flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
            location=-1,
            max_width=min(getSetting("popup_max_width",
                                     popup_default_max_width), width),
            max_height=min(getSetting("popup_max_height",
                                      popup_default_max_height), height - 100),
            on_navigate=self.on_navigate,
            on_hide=self.on_hide
        )

    def on_hide(self):
        self.currentSymbol = ''
        self.history = []

    def on_navigate(self, url):
        if re.search('^https?://', url):
            webbrowser.open_new(url)
            return True

        # m = re.search('^(changeto|constant)\.(.*)', url)
        # if m:
        #     if m.group(1) == 'changeto':
        #         symbol, content = getSymbolDescription(
        #             self.currentSymbol, m.group(2))
        #     else:
        #         self.view.run_command('docphp_insert', {"string": m.group(2)})
        #         self.view.hide_popup()

        # elif url == 'history.back':
        #     symbol = self.history.pop()
        #     self.currentSymbol = symbol
        # else:
        #     self.history.append(self.currentSymbol)
        #     symbol = url[:url.find('.html')]
        #     self.currentSymbol = symbol
        # symbol, content = getSymbolDescription(symbol)

        # if content == False:
        #     return False

        # content = self.formatPopup(
        #     content, symbol=symbol, can_back=len(self.history) > 0)

        # content = content[:65535]
        # self.view.update_popup(content)

    def formatPopup(self, content, symbol, can_back=False):
        if not isinstance(content, str):
            return

        content = decodeEntity(content)
        # content = decodeEntity(content, 'html')
        # return content

        parser = PopupHTMLParser(symbol, can_back)
        try:
            parser.feed(content)
        except FinishError:
            pass
        content = parser.output
        # content = '<body class="_app _mobile" style="max-width:700px"><style>' + sublime.load_resource(getPackagePath() + '/style-2.css') + \
        #     '</style><div class="_container" style="display: block"><div class="_content"><div class="_page _php">' + \
        #     content + "</div></div></div></body>"
        if getSetting("use_style"):
            print("Use custom style")
            content = '<style>' + sublime.load_resource(getPackagePath() + '/style.css') + \
                '</style><div id="outer"><div id="container">' + content + "</div></div>"
        content = re.sub('<strong><code>([A-Z_]+)</code></strong>',
                         '<strong><code><a class="constant" href="constant.\\1">\\1</a></code></strong>', content)
        # print(content)
        return content


class DevdocsSearchSymbolCommand(sublime_plugin.TextCommand):
    allSymbol = None

    def run(self, edit):
        language, language_type = parseViewLanguage(self.view)
        allSymbol = getAllSymbol(language)
        self.allSymbol = allSymbol
        print(allSymbol)
        sublime.Window.show_quick_panel(
            sublime.active_window(),
            allSymbol,
            on_select=self.on_select
        )

    def on_select(self, selectKey):
        if selectKey == -1:
            return False
        self.view.run_command("devdocs_show_definition", {
                              "symbol": self.allSymbol[selectKey]})


class DevdocsSetDefaultVersion(sublime_plugin.TextCommand):
    matchResult = None
    selected_language_type = None
    selected_language_version = None

    def run(self, edit):
        language, language_type = parseViewLanguage(self.view)
        matchResult = searchInAllLanguages(language_type, 'set_as_default')

        self.matchResult = matchResult
        print(matchResult)
        sublime.Window.show_quick_panel(
            sublime.active_window(),
            matchResult,
            on_select=self.on_select
        )

    def on_select(self, selectKey):
        if selectKey == -1:
            return False
        language, language_type = parseViewLanguage(self.view)
        selected_value = self.matchResult[selectKey]
        print('Selected ' + selected_value[0])
        if selected_value[1] == installed_tip['set_as_default']:
            setLanguageDefaultVersion(language_type, selected_value[0])
        else:
            selected_language_type = language_type
            selected_language_version = selected_value[0]
            sublime.set_timeout_async(self.installLanguageAndSetAsDefault, 0)

    def installLanguageAndSetAsDefault(self):
        if not self.selected_language_version or not self.selected_language_type:
            return False
        if installLanguage(self.selected_language_version):
            setLanguageDefaultVersion(
                self.selected_language_type, self.selected_language_version)


class DevdocsSetSyntaxAlias(sublime_plugin.TextCommand):
    all_languages_distinct = None
    selected_language_version = None

    def run(self, edit):
        all_languages_distinct = self.getAllLanguagesDistinct()
        self.all_languages_distinct = all_languages_distinct
        print(all_languages_distinct)
        sublime.Window.show_quick_panel(
            sublime.active_window(),
            all_languages_distinct,
            on_select=self.on_select
        )

    def getAllLanguagesDistinct(self):
        if self.all_languages_distinct == None:
            self.all_languages_distinct = []
            tmp_map = {}
            languages = getAllLanguages()
            for key, language in enumerate(languages):
                languageName = language.split("@", 1)[0]
                if not tmp_map.get(languageName):
                    self.all_languages_distinct.append(
                        [languageName, "Set now syntax alias this language"])
                    tmp_map[languageName] = True

        return self.all_languages_distinct

    def on_select(self, selectKey):
        if selectKey == -1:
            return False
        language = self.all_languages_distinct[selectKey]
        print('Selected ' + language[0])
        setSyntaxAlias(self.view.settings().get('syntax'), language[0])


class DevdocsShowAllLanguages(sublime_plugin.TextCommand):
    all_languages_display = None
    selected_language_version = None

    def run(self, edit):
        all_languages_display = checkAllLanguagesForDisplay()
        self.all_languages_display = all_languages_display
        print(all_languages_display)
        sublime.Window.show_quick_panel(
            sublime.active_window(),
            all_languages_display,
            on_select=self.on_select
        )

    def on_select(self, selectKey):
        if selectKey == -1:
            return False
        language = self.all_languages_display[selectKey]
        print('Selected ' + language[0])
        if language[1] == installed_tip['toggle']:
            uninstallLanguage(language[0])
        else:
            self.selected_language_version = language[0]
            sublime.set_timeout_async(self.installLanguage, 0)

    def installLanguage(self):
        installLanguage(self.selected_language_version)


class PopupHTMLParser(HTMLParser):
    symbol = ''
    can_back = False
    stack = []
    output = ''
    as_div = ['blockquote', 'tr', 'li', 'ul', 'dl',
              'dt', 'dd', 'table', 'tbody', 'thead']
    strip = ['td']
    started = False

    def __init__(self, symbol, can_back):
        self.symbol = symbol
        self.can_back = can_back
        super().__init__()

    def parseAttrs(self, attrs):
        ret = {}
        for k, v in attrs:
            ret[k] = v
        return ret

    def handle_starttag(self, tag, attrs):
        attrs = self.parseAttrs(attrs)

        for k in attrs:
            v = attrs[k]
            if k == 'id' and v == self.symbol:
                self.output = ''
            if k == 'class' and v == 'up':
                self.output = ''

        if tag in self.as_div:
            if 'class' in attrs:
                attrs['class'] += ' ' + tag
            else:
                attrs['class'] = tag
            tag = 'div'
        if tag in self.strip:
            return

        self.stack.append({'tag': tag, 'attrs': attrs})
        border = self.shall_border(tag, attrs)
        if border:
            self.output += '<div class="border border-' + border + '">'
        self.output += self.get_tag_text(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.as_div:
            tag = 'div'
        if tag in self.strip:
            return
        try:
            while(True):
                previous = self.stack.pop()
                self.output += '</' + tag + '>'

                # if re.search('h[1-6]', tag):
                #     self.output += '<div class="horizontal-rule"></div>'

                if self.shall_border(previous['tag'], previous['attrs']):
                    self.output += '</div>'
                for k in previous['attrs']:
                    v = previous['attrs'][k]
                    if k == 'id' and v == self.symbol:
                        pass
                        # raise FinishError
                    if k == 'class' and v == 'up':
                        self.navigate_up = self.output
                if tag == previous['tag']:
                    break

        except IndexError:
            pass

    def handle_startendtag(self, tag, attrs):
        if tag in self.as_div:
            if 'class' in attrs:
                attrs['class'] += ' ' + tag
            else:
                attrs['class'] = tag
            tag = 'div'
        self.output += self.get_tag_text(tag, attrs, True)

    def handle_data(self, data):
        self.output += data
        pass

    def handle_entityref(self, name):
        self.output += '&' + name + ';'

    def handle_charref(self, name):
        self.output += '&' + name + ';'

    def shall_border(self, tag, attrs):
        if tag.lower() not in ['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return False
        for k in attrs:
            v = attrs[k]
            if k == 'class':
                if re.search('\\b(phpcode|classsynopsis|methodsynopsis|note|informaltable)\\b', v):
                    return 'gray'
                elif re.search('\\b(tip)\\b', v):
                    return 'blue'
                elif re.search('\\b(warning)\\b', v):
                    return 'pink'
                elif re.search('\\b(caution)\\b', v):
                    return 'yellow'
        return False

    def get_tag_text(self, tag, attrs, is_startend=False):
        return '<' + (tag + ' ' + ' '.join(map(lambda m: m + '="' + re.sub('(?<!\\\\)"', '\\"', attrs[m]) + '"', attrs))).rstrip() + (' />' if is_startend else '>')


class FinishError(Exception):

    """For stopping the HTMLParser"""
    pass
