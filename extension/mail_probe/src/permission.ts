import { installPermissionPrompt } from './permission_prompt.js';
import type { PermissionRequester } from './permission_prompt.js';

declare const messenger: { permissions: PermissionRequester };

const button = document.getElementById('allow_send');
const status = document.getElementById('permission_status');
if (!(button instanceof HTMLButtonElement) || !status) {
  throw new Error('The permission prompt is incomplete.');
}
installPermissionPrompt(button, status, messenger.permissions);
