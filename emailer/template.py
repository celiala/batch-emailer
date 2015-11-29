import re

from emailer.config import ConfigGenerator
from emailer.email import EmailSender

class TextFormatter(object):

    FIELD_DELIMITER = "\t"              # .tsv file is tab-delimited
    PARAM_PATTERN = "{{([a-z_0-9]*)}}"  # formatter looks for keys in double-braces: {{key}}
    REPLACE_PATTERN = "{{%s}}"          # formatter extracts key from {{key}}, uses that to lookup
                                        # key + value from .tsv file

    def __init__(self, config):
        self.extra_params = {str(k): str(config.extra_param_settings[k])
                             for k in config.extra_param_settings}
        self.missing_keys = []
        self.missing_resources = []
        self.missing_tsv_keys = []

        # get the raw text, we'll format this into an array in get_entries
        content = self.get_resource_content(config, ConfigGenerator.TSV_FILE)
        if content:
            self.entries = self.get_entries(content,
                                            self.missing_tsv_keys,
                                            EmailSender.REQUIRED_PARAMS)

        # we use split b/c we only want the first line
        content = self.get_resource_content(config, ConfigGenerator.SUBJECT_FILE)
        if content:
            self.subject_template = content.split('\n')[0]

        # body can be either html or text; search for both
        content = None
        for f in ConfigGenerator.BODY_FILE:
            content = self.get_resource_content(config, f['filename'],
                                                log_as_missing=False)
            if content:
                self.body_template = content
                self.is_html = f['is_html']
                break
        if not content:
            body_resources = "email body (either %s)" \
                             % " or ".join([f['filename'] for f in ConfigGenerator.BODY_FILE])
            self.missing_resources.append(body_resources)

    def get_body(self, entry):
        return self.replace_keys(self.body_template, entry)

    def get_subject(self, entry):
        return self.replace_keys(self.subject_template, entry)

    def lookup_key(self, key, entry_values):
        if key in entry_values:
            return entry_values[key]
        if key in self.extra_params:
            return self.extra_params[key]
        return None

    def replace_keys(self, phrase, entry_values):
        phrase_keys = re.findall(self.PARAM_PATTERN, phrase)
        missing_keys = []
        for key in phrase_keys:
            key_replaced = False
            param_value = self.lookup_key(key, entry_values)
            try:
                phrase = re.sub(self.REPLACE_PATTERN % key, param_value, phrase)
                key_replaced = True
            except UnicodeDecodeError:
                pass
            if not key_replaced:
                missing_keys.append(key)
        if missing_keys:
            self.missing_keys.extend([k for k in missing_keys if k not in self.missing_keys])
        return phrase

    def get_resource_content(self, config, filename, log_as_missing=True):
        paths = config.get_resource_paths(filename)
        if paths:
            file_path = paths[0]
            with open(file_path, 'r') as f:
                return f.read()
        if log_as_missing:
            self.missing_resources.append(filename)
        return None

    @staticmethod
    def get_entries(tsv_content, required_keys=None, missing_keys=None):
        if not required_keys:
            required_keys = []
        if not missing_keys:
            missing_keys = []

        # get data (ignoring empty rows)
        data = [x for x in tsv_content.split('\n') if x]
        if not data:
            missing_keys.extend(required_keys)
            return []
        keys = [x.strip() for x in data[0].split(TextFormatter.FIELD_DELIMITER)]
        for param in required_keys:
            if param not in keys:
                missing_keys.append(param)

        # a list of key:value dicts for each mailing_list entry
        return [{keys[i]:TextFormatter.remove_junk(y)
                 for i, y in enumerate(x.split(TextFormatter.FIELD_DELIMITER))}
                for x in data[1:]]

    @staticmethod
    def remove_junk(text):
        return re.sub(r"[\x80-\xff]", ' ', text).strip()
