export interface PermissionRequester {
  request: (permissions: { permissions: string[] }) => Promise<boolean>;
}

export function installPermissionPrompt(
  button: HTMLButtonElement,
  status: HTMLElement,
  permissions: PermissionRequester,
) {
  button.addEventListener('click', () => {
    button.disabled = true;
    void permissions
      .request({ permissions: ['messages.send'] })
      .then((granted) => {
        status.textContent = granted
          ? 'Background sending is allowed for this fictional-mail probe.'
          : 'Background sending was not allowed.';
      })
      .catch(() => {
        status.textContent = 'The background sending permission request failed.';
      })
      .finally(() => {
        button.disabled = false;
      });
  });
}
