# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
from email.message import EmailMessage
from email.utils import make_msgid
import datetime
import email
import email.policy
import logging
import re
import smtplib
from socket import gaierror, timeout
from ssl import SSLError
import sys
import threading

import html2text
import idna

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import ustr, pycompat, formataddr

_logger = logging.getLogger(__name__)
address_pattern = re.compile(r'([^ ,<@]+@[^> ,]+)')
_test_logger = logging.getLogger('odoo.tests')


def extract_rfc2822_addresses(text):
    """Returns a list of valid RFC2822 addresses
       that can be found in ``source``, ignoring
       malformed ones and non-ASCII ones.
    """
    if not text:
        return []
    candidates = address_pattern.findall(ustr(text))
    return [formataddr(('', c), charset='ascii') for c in candidates]


def is_ascii(s):
    return all(ord(cp) < 128 for cp in s)


class MailServerInh(models.Model):
    _inherit = 'ir.mail_server'

    user_id_ept = fields.Many2one('res.users')

    # @api.model
    # def send_email(self, cr, uid, message, mail_server_id=None, smtp_server=None, smtp_port=None,
    #                smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
    #                context=None):
    #     print('Hello')
    #     mail_server = mail_server_id
    #     if not mail_server:
    #         user_obj = self.pool.get('res.users').browse(cr, uid, uid)
    #         email = user_obj.partner_id and user_obj.partner_id.email or False
    #         if email:
    #             mail_server_ids = self.search(cr, SUPERUSER_ID, [('user_id_ept', '=', uid)], order='sequence', limit=1)
    #             if mail_server_ids:
    #                 mail_server = mail_server_ids[0]
    #     return super(MailServerInh, self).send_email(cr, uid, message,
    #                                                  mail_server_id=mail_server,
    #                                                  context=context)

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):
    #     print('Hahaha')
    #     mail_server = mail_server_id
    #     if not mail_server:
    #         user_obj = self.env['res.users'].browse([self.env.user.id])
    #         email = user_obj.partner_id and user_obj.partner_id.email or False
    #         print(email)
    #         if email:
    #             print('in')
    #             mail_server_ids = self.env['ir.mail_server'].search([()], order='sequence', limit=1)
    #             print(mail_server_ids)
    #             if mail_server_ids:
    #                 mail_server = mail_server_ids[0]
    #     return super(MailServerInh, self).send_email(message, mail_server_id=mail_server.id, smtp_server=smtp_server, smtp_port=smtp_port,
    #                smtp_user=smtp_user, smtp_password=smtp_password, smtp_encryption=smtp_encryption, smtp_debug=smtp_debug,
    #                smtp_session=smtp_session)

        # print(smtp_user)
        # print(message)
        # print(mail_server_id)
        # print(smtp_server)
        """Sends an email directly (no queuing).

        No retries are done, the caller should handle MailDeliveryException in order to ensure that
        the mail is never lost.

        If the mail_server_id is provided, sends using this mail server, ignoring other smtp_* arguments.
        If mail_server_id is None and smtp_server is None, use the default mail server (highest priority).
        If mail_server_id is None and smtp_server is not None, use the provided smtp_* arguments.
        If both mail_server_id and smtp_server are None, look for an 'smtp_server' value in server config,
        and fails if not found.

        :param message: the email.message.Message to send. The envelope sender will be extracted from the
                        ``Return-Path`` (if present), or will be set to the default bounce address.
                        The envelope recipients will be extracted from the combined list of ``To``,
                        ``CC`` and ``BCC`` headers.
        :param smtp_session: optional pre-established SMTP session. When provided,
                             overrides `mail_server_id` and all the `smtp_*` parameters.
                             Passing the matching `mail_server_id` may yield better debugging/log
                             messages. The caller is in charge of disconnecting the session.
        :param mail_server_id: optional id of ir.mail_server to use for sending. overrides other smtp_* arguments.
        :param smtp_server: optional hostname of SMTP server to use
        :param smtp_encryption: optional TLS mode, one of 'none', 'starttls' or 'ssl' (see ir.mail_server fields for explanation)
        :param smtp_port: optional SMTP port, if mail_server_id is not passed
        :param smtp_user: optional SMTP user, if mail_server_id is not passed
        :param smtp_password: optional SMTP password to use, if mail_server_id is not passed
        :param smtp_debug: optional SMTP debug flag, if mail_server_id is not passed
        :return: the Message-ID of the message that was just sent, if successfully sent, otherwise raises
                 MailDeliveryException and logs root cause.
        """
        # Use the default bounce address **only if** no Return-Path was
        # provided by caller.  Caller may be using Variable Envelope Return
        # Path (VERP) to detect no-longer valid email addresses.

        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        mail_server_ids = self.env['ir.mail_server'].search([('user_id_ept', '=', user.id)])

        if mail_server_ids:
            smtp_from =  user.partner_id.email
        else:
            smtp_from = message['Return-Path'] or self._get_default_bounce_address() or message['From']
        assert smtp_from, "The Return-Path or From header is required for any outbound email"

        # if mail_server_ids:
        #     smtp_from = user.partner_id.email
        # The email's "Envelope From" (Return-Path), and all recipient addresses must only contain ASCII characters.
        from_rfc2822 = extract_rfc2822_addresses(smtp_from)
        assert from_rfc2822, ("Malformed 'Return-Path' or 'From' address: %r - "
                              "It should contain one valid plain ASCII email") % smtp_from
        # use last extracted email, to support rarities like 'Support@MyComp <support@mycompany.com>'
        smtp_from = from_rfc2822[-1]
        email_to = message['To']
        email_cc = message['Cc']
        email_bcc = message['Bcc']
        del message['Bcc']

        smtp_to_list = [
            address
            for base in [email_to, email_cc, email_bcc]
            for address in extract_rfc2822_addresses(base)
            if address
        ]
        assert smtp_to_list, self.NO_VALID_RECIPIENT

        x_forge_to = message['X-Forge-To']
        if x_forge_to:
            # `To:` header forged, e.g. for posting on mail.channels, to avoid confusion
            del message['X-Forge-To']
            del message['To']  # avoid multiple To: headers!
            message['To'] = x_forge_to

        # Do not actually send emails in testing mode!
        if getattr(threading.currentThread(), 'testing', False) or self.env.registry.in_test_mode():
            _test_logger.info("skip sending email in test mode")
            return message['Message-Id']

        try:
            message_id = message['Message-Id']
            smtp = smtp_session
            if mail_server_ids:
                mail_server_id = mail_server_ids[0]

                smtp = self.connect(
                    mail_server_id.smtp_host, mail_server_id.smtp_port, mail_server_id.smtp_user, mail_server_id.smtp_pass,
                    mail_server_id.smtp_encryption, mail_server_id.smtp_debug, mail_server_id=mail_server_id.id)
            else:
                smtp = smtp or self.connect(
                    smtp_server, smtp_port, smtp_user, smtp_password,
                    smtp_encryption, smtp_debug, mail_server_id=mail_server_id)
            # print(smtp)
            if sys.version_info < (3, 7, 4):
                # header folding code is buggy and adds redundant carriage
                # returns, it got fixed in 3.7.4 thanks to bpo-34424
                message_str = message.as_string()
                message_str = re.sub('\r+(?!\n)', '', message_str)

                mail_options = []
                if any((not is_ascii(addr) for addr in smtp_to_list + [smtp_from])):
                    # non ascii email found, require SMTPUTF8 extension,
                    # the relay may reject it
                    mail_options.append("SMTPUTF8")
                smtp.sendmail(smtp_from, smtp_to_list, message_str, mail_options=mail_options)
            else:
                smtp.send_message(message, smtp_from, smtp_to_list)

            # do not quit() a pre-established smtp_session
            if not smtp_session:
                smtp.quit()
        except smtplib.SMTPServerDisconnected:
            raise
        except Exception as e:
            params = (ustr(smtp_server), e.__class__.__name__, ustr(e))
            msg = _("Mail delivery failed via SMTP server '%s'.\n%s: %s", *params)
            _logger.info(msg)
            raise MailServerInh(_("Mail Delivery Failed"), msg)
        return message_id
