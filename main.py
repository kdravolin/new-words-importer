import re
import urllib
from urllib import request, parse
import json
from http.cookiejar import CookieJar

import config


class Lingualeo:
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._cookie = CookieJar()

    def auth(self):
        url = "http://api.lingualeo.com/api/login"
        values = {
            "email": self._email,
            "password": self._password
        }
        return self.get_content(url, values)

    def add_word(self, word, tword):
        url = "http://api.lingualeo.com/addword"
        values = {
            "word": word,
            "tword": tword
        }
        self.get_content(url, values)

    def get_translates(self, word, use_base_form=True):
        url = "http://api.lingualeo.com/gettranslates?word=" + urllib.parse.quote_plus(word)

        try:
            result = self.get_content(url, {})

            if not result["translate"]:
                return None

            first_translate = result["translate"][0]

            if result["word_forms"] and use_base_form:
                word_form = result["word_forms"][0]['word']

                if word_form != word:
                    print("Using base form of word '{}': {}".format(word, word_form))
                    return self.get_translates(word_form)

            return {
                "is_exist": first_translate["is_user"],
                "word": word,
                "tword": first_translate["value"].encode("utf-8")
            }
        except Exception:
            return None

    def get_content(self, url, values):
        data = urllib.parse.urlencode(values)
        cookie_processor = urllib.request.HTTPCookieProcessor(self._cookie)
        opener = urllib.request.build_opener(cookie_processor)
        binary_data = data.encode('utf-8')
        req = opener.open(url, binary_data)
        req_data = req.read().decode('utf-8')
        return json.loads(req_data)


class WordHandler:
    def __init__(self):
        self._words = []

    @property
    def words(self):
        return self._words

    def read(self, source):
        with open(source) as f:
            for line in f.readlines():
                for w in re.findall(r'([A-Za-z]+)', line):
                    w = w.lower()

                    if len(w) > 1 and w not in self._words:
                        self._words.append(w)

word_handler = WordHandler()
word_handler.read(config.srt_path)

lingualeo = Lingualeo(config.email, config.password)
lingualeo.auth()

for index, word in enumerate(word_handler.words):
    translate = lingualeo.get_translates(word)
    progress = index / len(word_handler.words)
    word = translate["word"]

    if not translate:
        print("{:.2%} | Translate doesn't exist: {}".format(progress, word))
    elif translate["is_exist"]:
        print("{:.2%} | Already exists: {}".format(progress, word))
    else:
        lingualeo.add_word(word, translate["tword"])
        print("{:.2%} | Add word: {}".format(progress, word))
