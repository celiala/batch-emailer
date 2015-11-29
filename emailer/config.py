import json
from os.path import (dirname, abspath, isfile, join)


"""
this file tries to find the config settings for the emailer.
If it can't find one, it generates one. It also asks the user
which folder to store the config.

"""
class ConfigKeys(object):
    EXTRA_PARAMS_KEY = "TEMPLATE_PARAMS"
    EMAIL_DRY_RUNS_TO = "EMAIL_DRY_RUNS_TO"
    SMTP_PASSWORD = "SMTP_PASSWORD"
    SMTP_EMAIL = "SMTP_EMAIL"
    EMAIL_BASE_CC = "EMAIL_BASE_CC"
    SMTP_SERVER = "SMTP_SERVER"


class ConfigGenerator(object):

    EMAILER_CONFIG = "config.json"
    CONFIG_PROMPTS = "emailer/config.json"
    PROMPT_TYPES = ["required", "nullable"]

    # used by TextFormatter
    SUBJECT_FILE = "subject.txt"
    BODY_FILE = [
        {"filename": "body.html",
         "is_html": True},
        {"filename": "body.txt",
         "is_html": False}
    ]
    TSV_FILE = "recipients.tsv"

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.path_options = self.get_config_folders(self.data_folder)
        self.emailer_settings = self.get_emailer_settings()
        self.extra_param_settings = self.get_extra_param_settings()

    def get(self, key):
        if key in self.emailer_settings:
            return self.emailer_settings[key]
        if key in self.extra_param_settings:
            return self.extra_param_settings[key]
        return None

    def get_emailer_settings(self):
        settings = self.get_settings_from_resource(self.EMAILER_CONFIG)
        prompt_keys = self.get_prompt_keys()
        missing_keys = self.get_missing(settings.keys(), prompt_keys)
        if not missing_keys:
            return settings
        print "the following keys are missing:", ", ".join(missing_keys)

        settings = self.get_config_from_prompts(settings)
        folder_to_save_config = self.get_folder_to_save_config()
        self.save_json(join(folder_to_save_config, self.EMAILER_CONFIG), settings)
        return settings

    @staticmethod
    def get_missing(full_set, subset):
        return [k for k in subset if k not in full_set]

    def get_extra_param_resource(self):
        if ConfigKeys.EXTRA_PARAMS_KEY in self.emailer_settings:
            return self.emailer_settings[ConfigKeys.EXTRA_PARAMS_KEY]

    def get_extra_param_settings(self, extra_params_json_resource=None):
        if not extra_params_json_resource:
            extra_params_json_resource = self.get_extra_param_resource()
        if not extra_params_json_resource:
            return {}
        return self.get_settings_from_resource(extra_params_json_resource)

    def get_settings_from_resource(self, filename, overwrite=False):
        config_settings = {}
        paths = self.get_resource_paths(filename)
        for path in paths:
            self.extend(config_settings, self.get_json(path), overwrite)
        return config_settings

    def get_resource_paths(self, filename):
        folders = self.path_options
        paths = []
        for folder in folders:
            path = join(folder, filename)
            if isfile(path):
                paths.append(path)
        return paths

    def get_prompts(self):
        return json.load(open(self.CONFIG_PROMPTS, 'r'))

    def get_prompt_keys(self, prompt_type=None):
        if prompt_type:
            types = [prompt_type]
        else:
            types = self.PROMPT_TYPES
        prompts = self.get_prompts()
        return [p["key"] for t in types for p in prompts[t]]

    def get_config_from_prompts(self, config_settings=None, overwrite=False):
        prompts = self.get_prompts()
        if not config_settings:
            config_settings = {}
        for prompt_type in ConfigGenerator.PROMPT_TYPES:
            prompt_keys = self.get_prompt_keys(prompt_type)
            missing_keys = self.get_missing(config_settings, prompt_keys)
            if overwrite or missing_keys:
                print "The following settings are", prompt_type
                config_settings = ConfigGenerator.get_config_from_prompt(
                    config_settings,
                    prompts[prompt_type],
                    prompt_type == "required",
                    overwrite)
        return config_settings

    def get_folder_to_save_config(self):
        i = 0
        for option in self.path_options:
            if not option.endswith("/"):
                i += 1
                print i, "-", option
        i = int(raw_input("Enter which folder you want to save the final config? "))
        return self.path_options[i-1]

    @staticmethod
    def get_config_from_prompt(config_settings,
                               prompts, is_required,
                               overwrite):
        for prompt in prompts:
            if overwrite or prompt["key"] not in config_settings:
                value = None
                while True:
                    output = prompt["key"] + ": " + prompt["prompt"]
                    if "default" in prompt:
                        output += " (" + prompt["default"] + ")"
                    value = raw_input(output + ": ")
                    if value == '':
                        value = None
                    if not value and "default" in prompt:
                        value = prompt["default"]
                    if is_required and not value:
                        pass
                    else:
                        break
                config_settings[prompt["key"]] = value
        return config_settings

    @staticmethod
    def get_config_folders(data_folder):
        root_folder = abspath(".")
        path = data_folder
        path_options = []
        while root_folder in abspath(path):
            path_options.append(path)
            path = dirname(path)
            if not path:
                break
        path_options.append('.')
        return path_options

    @staticmethod
    def extend(dict1, dict2, overwrite):
        for k in dict2:
            if overwrite or k not in dict1:
                dict1[k] = dict2[k]
        return dict1

    @staticmethod
    def get_json(path):
        return json.load(open(path, 'r'))

    @staticmethod
    def save_json(path, data):
        json.dump(data, open(path, 'w'), indent=2)

    @staticmethod
    def print_dict(d):
        for k in d:
            print k, d[k]

