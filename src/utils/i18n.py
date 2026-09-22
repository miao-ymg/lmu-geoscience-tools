import os
import sys
import json
from PyQt6.QtCore import QObject, pyqtSignal, QSettings

def _resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class I18nManager(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("LMU", "GeoscienceTools")
        self.current_lang = self.settings.value("language", "en")
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        for lang in ["en", "de"]:
            path = _resource_path(os.path.join("resources", "translations", f"{lang}.json"))
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
            except Exception as e:
                print(f"Error loading {lang} translations from {path}: {e}")
                self.translations[lang] = {}

    def get_language(self) -> str:
        return self.current_lang

    def set_language(self, lang: str):
        if lang not in ["en", "de"]:
            return
        if self.current_lang != lang:
            self.current_lang = lang
            self.settings.setValue("language", lang)
            self.language_changed.emit(lang)

    def tr(self, key: str, **kwargs) -> str:
        lang_dict = self.translations.get(self.current_lang, {})
        text = lang_dict.get(key)
        if text is None:
            # Fallback to English
            text = self.translations.get("en", {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text

# Global singleton instance
i18n = I18nManager()

def tr(key: str, **kwargs) -> str:
    return i18n.tr(key, **kwargs)
