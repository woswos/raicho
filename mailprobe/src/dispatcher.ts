import type { MailApi } from './mail_api.js';
import type { Command } from './validation.js';
import { integerValue, stringValue } from './validation.js';
import { messageDetails } from './message_details.js';
import { collectMessages, inspectMessage, queryDetails } from './message_queries.js';

export async function dispatchCommand(api: MailApi, command: Command): Promise<unknown> {
  const parameters = command.arguments;
  switch (command.action) {
    case 'permission_status':
      return {
        send_allowed: await api.permissions.contains({
          permissions: ['messages.send'],
        }),
      };
    case 'open_permission_page':
      await api.runtime.openOptionsPage();
      return { opened: true };
    case 'inventory':
      return {
        accounts: await api.accounts.list(true),
        api: {
          saveMessage: typeof api.messages.saveMessage,
          sendMessage: typeof api.messages.sendMessage,
        },
      };
    case 'save':
      return api.messages.saveMessage(messageDetails(parameters.details), {
        mode: 'draft',
      });
    case 'send': {
      const mode = parameters.mode;
      if (mode !== 'sendNow' && mode !== 'sendLater') throw new Error('An explicit send mode is required.');
      if (typeof api.messages.sendMessage !== 'function')
        throw new Error('Background send permission has not been granted.');
      return api.messages.sendMessage(messageDetails(parameters.details), {
        mode,
      });
    }
    case 'query':
      return collectMessages(api, await api.messages.query(queryDetails(parameters.query ?? {})));
    case 'list':
      return collectMessages(api, await api.messages.list(stringValue(parameters.folder_id)));
    case 'get_message':
      return inspectMessage(api, integerValue(parameters.message_id));
    case 'begin_new': {
      const tab = await api.compose.beginNew(
        integerValue(parameters.message_id),
        messageDetails(parameters.details ?? {}, false),
      );
      return { tab, details: await api.compose.getComposeDetails(tab.id) };
    }
    case 'update_compose': {
      const identifier = integerValue(parameters.tab_id);
      await api.compose.setComposeDetails(identifier, messageDetails(parameters.details, false));
      return api.compose.getComposeDetails(identifier);
    }
    case 'save_compose':
      return api.compose.saveMessage(integerValue(parameters.tab_id), {
        mode: 'draft',
      });
    case 'inspect_native_compose': {
      const tabs =
        parameters.tab_id === undefined
          ? (await api.tabs.query({})).filter((tab) => tab.type === 'messageCompose')
          : [{ id: integerValue(parameters.tab_id) }];
      return Promise.all(
        tabs.map(async (tab) => ({
          tab,
          details: await api.compose.getComposeDetails(tab.id),
        })),
      );
    }
    case 'close_compose':
      await api.tabs.remove(integerValue(parameters.tab_id));
      return { closed: true };
    case 'select_draft': {
      const tab = (await api.mailTabs.query({}))[0];
      if (!tab) throw new Error('No native mail tab is available.');
      await api.mailTabs.setSelectedMessages(tab.id, [integerValue(parameters.message_id)]);
      return { tab };
    }
    case 'select_folder': {
      const tab = (await api.mailTabs.query({}))[0];
      if (!tab) throw new Error('No native mail tab is available.');
      return {
        tab: await api.mailTabs.update(tab.id, {
          displayedFolder: stringValue(parameters.folder_id),
          folderMode: 'all',
        }),
      };
    }
    default:
      throw new Error('Unsupported probe command.');
  }
}
