import re
import json
import urllib

language_slug_alias_default = {
    "apache": "apache_http_server",
    "jquery_core": "jquery",
    "jquery_mobile": "jquerymobile",
    "jquery_ui": "jqueryui",
    "nokogiri2": "nokogiri",
    "support_tables": "browser_support_tables",
}


def getSetting(key, default=None):
    return default


def getLanguageSlug(language):
    global language_slug_alias_default
    language_slug_alias = language_slug_alias_default.copy()
    language_slug_alias.update(getSetting('language_slug_alias', {}))
    if language_slug_alias.get(language):
        return language_slug_alias.get(language)
    if language[-1] == '@':
        language = language[:-1]
    v = language.split('@', 1)
    name = v[0].lower()
    if len(v) == 1:
        return name
    version = v[1].lower().replace(
        '@', '~').replace('+', 'p').replace('#', 's')
    version = re.sub(r"[^a-z0-9\_\.]", "_", version)
    return name + "~" + version


def getResponseCode(path):
    url = 'http://dl.devdocs.io/' + path + '.tar.gz'
    response = urllib.urlopen(url)
    code = response.getcode()
    return code


def main():
    badL = []
    with open("./languages.json", 'r') as content:
        languages = json.load(content)
        for lang in languages:
            path = getLanguageSlug(lang)
            code = getResponseCode(path)
            print("%s ToPath: %s ResponseCode: %d" % (lang, path, code))
            if code != 200:
                badL.append((lang, path, code))
    print(badL)

if __name__ == "__main__":
    main()
