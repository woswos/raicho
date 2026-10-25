def preferences():
    configured = {
        'mail.accountmanager.accounts': 'account1,account2',
        'mail.accountmanager.defaultaccount': 'account1',
        'mail.accountmanager.localfoldersserver': 'server2',
        'mail.account.account1.server': 'server1',
        'mail.account.account1.identities': 'id1,id2',
        'mail.account.account2.server': 'server2',
        'mail.server.server1.type': 'imap',
        'mail.server.server1.hostname': 'mail-proxy',
        'mail.server.server1.userName': 'sender',
        'mail.server.server1.name': 'Disposable mail fixture',
        'mail.server.server1.port': 3143,
        'mail.server.server1.socketType': 0,
        'mail.server.server1.authMethod': 3,
        'mail.server.server1.login_at_startup': True,
        'mail.server.server1.check_new_mail': False,
        'mail.server.server1.using_subscription': False,
        'mail.server.server1.directory-rel': '[ProfD]ImapMail/mail-proxy',
        'mail.server.server1.namespace.personal': '""',
        'mail.server.server1.override_namespaces': False,
        'mail.server.server1.offline_download': True,
        'mail.server.server2.type': 'none',
        'mail.server.server2.hostname': 'Local Folders',
        'mail.server.server2.userName': 'nobody',
        'mail.server.server2.name': 'Local Folders',
        'mail.server.server2.directory-rel': '[ProfD]Mail/Local Folders',
        'mail.smtpservers': 'smtp1',
        'mail.smtp.defaultserver': 'smtp1',
        'mail.smtpserver.smtp1.hostname': 'mail-proxy',
        'mail.smtpserver.smtp1.port': 3025,
        'mail.smtpserver.smtp1.try_ssl': 0,
        'mail.smtpserver.smtp1.authMethod': 1,
        'mail.smtpserver.smtp1.username': 'sender',
        'mail.shell.checkDefaultClient': False,
        'mail.rights.override': True,
        'mailnews.start_page.enabled': False,
        'mailnews.start_page.url': 'about:blank',
        'mailnews.start_page.override_url': 'about:blank',
        'mail.provider.enabled': False,
        'mail.accountcreation.enableNewAccountHub': False,
        'mail.spotlight.firstRunDone': True,
        'mailnews.message_display.disable_remote_image': True,
        'datareporting.policy.dataSubmissionEnabled': False,
        'datareporting.healthreport.uploadEnabled': False,
        'toolkit.telemetry.enabled': False,
        'toolkit.telemetry.unified': False,
        'browser.startup.homepage_override.mstone': 'ignore',
    }
    for identity, address in [
        ('id1', 'sender@raicho.test'),
        ('id2', 'alias@raicho.test'),
    ]:
        values = {
            'fullName': 'Raicho fixture',
            'useremail': address,
            'valid': True,
            'smtpServer': 'smtp1',
            'compose_html': True,
            'fcc': True,
            'fcc_folder': 'imap://sender@mail-proxy/Sent',
            'fcc_folder_picker_mode': '1',
            'draft_folder': 'imap://sender@mail-proxy/Drafts',
            'drafts_folder_picker_mode': '1',
            'stationery_folder': 'imap://sender@mail-proxy/Templates',
            'archive_folder': 'imap://sender@mail-proxy/Archives',
        }
        configured.update(
            {
                f'mail.identity.{identity}.{name}': value
                for name, value in values.items()
            }
        )
    return configured
