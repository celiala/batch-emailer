import smtplib

class SmtpConfig(object):

    def __init__(self, smtp_server, email, password):
        self.server = smtplib.SMTP(smtp_server)
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(email, password)

    def get_server(self):
        return self.server

    def __del__(self):
        self.server.quit()
