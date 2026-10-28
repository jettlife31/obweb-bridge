#!/usr/bin/env python3
"""Prepare an Outbreak Web identity. This is separate from packet forwarding."""
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import urllib.error
import urllib.request

REGISTER_URL = 'https://outbreakweb.com/api/kk/register'
NAME = re.compile(r'[A-Za-z0-9]{1,15}\Z')
TRANSFER = re.compile(r'REO1-([A-Za-z0-9]{1,15})-([0-9a-f]{32})\Z')


def credential(name, token):
    if not NAME.fullmatch(name) or not re.fullmatch(r'[0-9a-f]{32}', token):
        raise ValueError('Invalid identity')
    return hashlib.sha256(f'reo-web:{name}:{token}'.encode()).hexdigest()[:12]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def register(name, secret, opener=None):
    """Never print remote bodies, request bodies, headers or secrets."""
    request = urllib.request.Request(
        REGISTER_URL,
        data=json.dumps({'name': name, 'credential': secret}).encode(),
        headers={'Content-Type': 'application/json', 'Origin': 'https://outbreakweb.com',
                 'Referer': 'https://outbreakweb.com/file1/', 'User-Agent': 'Mozilla/5.0'},
        method='POST')
    opener = opener or urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def state_path():
    base = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    return base / 'outbreak-web-login' / 'identities.json'


def load_state(path):
    if not path.exists():
        return {'identities': {}}
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or not isinstance(value.get('identities'), dict):
        raise ValueError('Invalid local state')
    for name, token in value['identities'].items():
        credential(name, token)
    return value


def save_state(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, tmp = tempfile.mkstemp(prefix='.identity-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def login_from_environment():
    """Non-interactive account setup for containers and scripted launches."""
    name = os.environ.get('OBWEB_USERNAME', '')
    if not NAME.fullmatch(name):
        raise ValueError('OBWEB_USERNAME is required and must contain 1 to 15 letters or numbers.')

    transfer = os.environ.get('OBWEB_REO_CODE', '').strip()
    if transfer:
        match = TRANSFER.fullmatch(transfer)
        if not match:
            raise ValueError('OBWEB_REO_CODE must be the complete REO1 transfer code from the website.')
        if match[1] != name:
            raise ValueError('OBWEB_REO_CODE belongs to a different username than OBWEB_USERNAME.')

    path = state_path()
    state = load_state(path)
    if transfer:
        token = match[2]
    else:
        # Keep a generated identity stable across container restarts.
        token = state['identities'].get(name) or secrets.token_hex(16)

    state['identities'][name] = token
    save_state(path, state)
    secret = credential(name, token)
    print('Outbreak Web login — account setup, separate from the WSS tunnel.', flush=True)
    print('Registering/checking the username with Outbreak Web…', flush=True)
    status = register(name, secret)
    if status == 409:
        if transfer:
            raise ValueError(f'Username "{name}" already exists, but the supplied REO code was not accepted. Check the code and username.')
        raise ValueError(f'Username "{name}" already exists. Set OBWEB_REO_CODE to the matching REO transfer code, or choose another username.')
    if not 200 <= status < 300:
        raise ValueError(f'The service rejected registration (HTTP {status}); the gateway was not started.')

    state['last_name'] = name
    save_state(path, state)
    print('Account accepted. Enter these details on the game login screen:', flush=True)
    print(f'  Username: {name}', flush=True)
    print(f'  Password: {secret}', flush=True)
    print('This is the game password. Keep the container logs private.', flush=True)
    print('The game does not fill this in automatically. Use the patched game image.', flush=True)


def main():
    if os.geteuid() == 0:
        raise ValueError('Run the launcher as a regular user, without sudo.')
    if os.environ.get('OBWEB_RUN_MODE') == 'container':
        if os.environ.get('OBWEB_REO_CODE') and not os.environ.get('OBWEB_USERNAME'):
            raise ValueError('OBWEB_USERNAME is required when OBWEB_REO_CODE is set.')
        login_from_environment()
        return
    # All interactive credentials stay in the local terminal, not shell stdout/logs.
    with open('/dev/tty', 'w') as tty, open('/dev/tty', 'r') as tty_input:
        def say(text):
            tty.write(text + '\n'); tty.flush()
        def ask(text):
            tty.write(text); tty.flush()
            answer = tty_input.readline()
            if not answer:
                raise EOFError()
            return answer.strip()
        path = state_path()
        state = load_state(path)
        say('Outbreak Web login — account setup, separate from the WSS tunnel.')
        while True:
            previous = state.get('last_name', '')
            if previous and previous in state['identities']:
                mode = ask(f'Use saved account "{previous}"? [Y]es / [I]mport / [N]ew: ').lower()
                if mode in ('', 'y', 'yes'):
                    name = previous
                    token = state['identities'][name]
                elif mode in ('i', 'import'):
                    mode = 'i'
                elif mode in ('n', 'new'):
                    mode = 'n'
                else:
                    continue
            else:
                mode = ask('[N] New account / [I] Import existing account: ').lower()

            if mode in ('i', 'import'):
                transfer = getpass.getpass('Paste the complete REO1 transfer code: ', stream=tty).strip()
                match = TRANSFER.fullmatch(transfer)
                if not match:
                    say('Code not recognized. Copy the complete REO1 transfer code from the website.')
                    continue
                name, token = match.groups()
                say(f'Importing account "{name}".')
            elif mode in ('n', 'new'):
                name = ask('Choose a username (1–15 letters or numbers): ')
                if not NAME.fullmatch(name):
                    say('Username must contain 1 to 15 letters or numbers, with no spaces.')
                    continue
                token = secrets.token_hex(16)
            elif not (previous and mode in ('', 'y', 'yes')):
                continue

            # Persist BEFORE the request: a timeout must not lose the identity.
            state['identities'][name] = token
            save_state(path, state)
            secret = credential(name, token)
            say('Registering/checking the username with Outbreak Web…')
            status = register(name, secret)
            if status == 409:
                say('Username already registered with a different credential. Choose another username or import your code.')
                # Keep the pending identity on disk; explicit import may replace it.
                if ask('Import your code for this username? [y/N]: ').lower() == 'y':
                    transfer = getpass.getpass('REO1 code (hidden input): ', stream=tty).strip()
                    match = TRANSFER.fullmatch(transfer)
                    if match and match[1] == name:
                        state['identities'][name] = match[2]
                        save_state(path, state)
                continue
            if not 200 <= status < 300:
                raise ValueError(f'The service rejected registration (HTTP {status}); the gateway was not started.')
            state['last_name'] = name
            save_state(path, state)
            say('Account accepted. Enter these details on the game login screen:')
            say(f'  Username: {name}')
            say(f'  Password: {secret}')
            say('This is the game password. Keep it private; do not share screenshots of this screen.')
            say('The game does not fill this in automatically. Use the patched game image.')
            ask('Save these details, then press Enter to start the gateway:')
            return


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nLogin cancelled; the gateway was not started.')
        raise SystemExit(1)
    except (OSError, ValueError, urllib.error.URLError) as error:
        # Exception messages from network libraries may contain URLs/data; only
        # locally constructed validation messages are safe to display.
        detail = str(error) if type(error) is ValueError else type(error).__name__
        print(f'Login setup failed: {detail}')
        raise SystemExit(1)
