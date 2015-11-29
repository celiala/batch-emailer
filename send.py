import os
import sys

from emailer.email import EmailSender
from emailer.smtp import SmtpConfig
from emailer.template import TextFormatter
from emailer.config import ConfigGenerator, ConfigKeys

if len(sys.argv) < 2:
    print "Usage: python send.py [data_folder]"
    exit(1)

folder_name = sys.argv[1]
if not os.path.isdir(folder_name):
    print folder_name, "is not a valid folder"
    exit(1)

config = ConfigGenerator(folder_name)
sender = EmailSender(config.get(ConfigKeys.SMTP_EMAIL),
                     config.get(ConfigKeys.EMAIL_DRY_RUNS_TO),
                     config.get(ConfigKeys.EMAIL_BASE_CC))
formatter = TextFormatter(config)

errors = False
if formatter.missing_resources:
    errors = True
    print "Could not find the following resources:", ", ".join(formatter.missing_resources)

if formatter.missing_tsv_keys:
    errors = True
    print "Tsv file must have the following fields:", ", ".join(formatter.missing_tsv_keys)

if errors:
    exit(1)

is_html = formatter.is_html
entries = formatter.entries

def print_missing_keys():
    if formatter.missing_keys:
        print "These unset parameters were found in the subject/body:"
        print "\t", ", ".join(["{{%s}}" % k for k in formatter.missing_keys])
        print "Please set these in either",\
            ConfigGenerator.TSV_FILE, "or", config.get_extra_param_resource()

# print menu choices
print "1) Preview headers + data values"
print "2) Send dry-run emails"
print "3) Send real emails"

menu_choice = raw_input("Please select: ")
print "==================================================="
print "* * * * * * * * * * * * * * * * * * * * * * * * * *"
print "==================================================="
if menu_choice == '1':
    for entry in entries:
        # we don't need the email body, but running the method to
        # check for missing parameters
        formatter.get_body(entry=entry)

        subject = formatter.get_subject(entry=entry)
        all_ccs = sender.get_all_ccs(entry=entry)
        headers = sender.get_header(recipient=entry[EmailSender.KEY_RECIPIENT],
                                    all_ccs=all_ccs,
                                    subject=subject,
                                    include_mime_and_type=False,
                                    extra_params=entry)

        print "---------------------------------------------"
        print headers
    print "============================================="
    print "Body format:", "HTML" if is_html else "TEXT"
    print_missing_keys()
    print "============================================="

elif menu_choice in ['2', '3']:

    dry_run = True if menu_choice == '2' else False
    if not dry_run:
        confirm_real = raw_input("Please confirm (y) that you want to send real emails: ")
        if confirm_real != 'y':
            exit(0)

    smtp = SmtpConfig(config.get(ConfigKeys.SMTP_SERVER),
                      config.get(ConfigKeys.SMTP_EMAIL),
                      config.get(ConfigKeys.SMTP_PASSWORD))
    server = smtp.get_server()

    for entry in entries:
        subject = formatter.get_subject(entry)
        body = formatter.get_body(entry)
        if not formatter.missing_keys:
            sender.send(server=server,
                        entry=entry,
                        subject=subject,
                        body=body,
                        is_html=is_html,
                        dry_run=dry_run)
    print_missing_keys()
