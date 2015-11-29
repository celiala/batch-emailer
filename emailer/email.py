import re

class EmailSender(object):

    KEY_RECIPIENT = 'email_to'
    KEY_CC = 'email_cc'
    REQUIRED_PARAMS = [KEY_RECIPIENT, KEY_CC]

    def __init__(self, sender, dry_run_recipient, base_cc=None):
        self.sender = sender
        self.dry_run_recipient = dry_run_recipient
        if isinstance(base_cc, list):
            self.base_cc = base_cc
        elif base_cc:
            self.base_cc = [e.strip() for e in base_cc.split(',')]
        else:
            self.base_cc = []

    def get_all_ccs(self, entry):
        cc_emails = self.base_cc[:]
        if self.KEY_CC in entry:
            cc_emails.append(entry[self.KEY_CC])
        if cc_emails:
            return ', '.join(cc_emails)
        else:
            return None

    def get_header(self, recipient, all_ccs, subject, is_html=False, include_mime_and_type=True,
                   extra_params=None):

        content_type = 'text/html' if is_html else 'text/plain'
        headers = ["From: " + self.sender,
                   "To: " + recipient]
        if all_ccs:
            headers.append("CC: " + all_ccs)

        headers.append("Subject: " + subject)

        if include_mime_and_type:
            headers.extend(["mime-version: 1.0",
                            "content-type: " + content_type])

        if extra_params:
            for key in extra_params:
                if key not in [self.KEY_RECIPIENT, self.KEY_CC]:
                    headers.append(key + ": " + extra_params[key])

        return "\r\n".join(headers)

    def send(self, server, entry, subject, body, is_html=False, dry_run=True):

        all_ccs = self.get_all_ccs(entry=entry)
        recipient = entry[self.KEY_RECIPIENT]
        headers = self.get_header(recipient=recipient, all_ccs=all_ccs, subject=subject,
                                  is_html=is_html)

        if dry_run:
            print "REAL header (NOT USING):"
            print "==================================================="
            print headers

            recipient = self.dry_run_recipient
            all_ccs = None
            headers = self.get_header(recipient=recipient, all_ccs=all_ccs, subject=subject,
                                      is_html=is_html)
            print "==================================================="
            print "DRY-RUN header (USING THIS):"
            print "==================================================="
            print headers
        else:
            print "REAL EMAIL:"
            print headers
        print "--------------------------------------------------"
        print body

        confirm = raw_input("Do you really want to send this to %r? " % recipient)
        if confirm == 'y':
            #collect all emails in To, From, and CC fields
            all_emails_with_names = recipient + ',' + self.sender
            if all_ccs:
                all_emails_with_names += ',' + all_ccs
            just_emails = EmailSender.extract_just_emails(all_emails_with_names.split(','))
            server.sendmail(self.sender,
                            just_emails,
                            headers + "\r\n\r\n" + body)

    @staticmethod
    def extract_just_emails(emails):
        just_emails = []
        for full_email in emails:
            just_email = re.compile("<(.*)>").findall(full_email)
            if just_email:
                just_emails.append(just_email[0])
            elif '@' in full_email:
                just_emails.append(full_email)
        return just_emails
