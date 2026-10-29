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

from memory_card import ensure_account_cards, existing_account_cards

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
    for key in ('memory_cards', 'pending_memory_cards'):
        preferences = value.get(key, {})
        if not isinstance(preferences, dict) or any(type(flag) is not bool for flag in preferences.values()):
            raise ValueError('Invalid local memory-card preferences')
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


def generated_card_directory(container=False):
    if container:
        return state_path().parent / 'memcards'
    return Path(__file__).resolve().parent / 'generated-memcards'


def prepare_memory_card(name, container=False):
    try:
        paths, created = ensure_account_cards(name, generated_card_directory(container))
    except (OSError, ValueError):
        raise ValueError('Account saved, but memory-card generation failed. Check the output directory and retry; existing cards were preserved.') from None
    return paths, created


def show_memory_cards(paths, created, say, container=False):
    if not paths:
        say('Memory-card generation skipped; use your existing or exported memory card.')
        return
    for path in paths:
        say(f'  Memory card: {path}')
    say('Memory card created.' if created else 'Existing memory card preserved.')
    say('Select this card, create the in-game network configuration, then use Go Online with the password above.')
    if container:
        say('Memory cards are stored in the persistent volume. Copy them from another terminal while the container is running:')
        for path in paths:
            say(f'  docker cp CONTAINER_NAME:"{path}" ./{path.name}')
        say('Replace CONTAINER_NAME with the container name shown by docker ps.')


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
    pending = state.setdefault('pending_memory_cards', {})
    new_account = not transfer and name not in state['identities']
    if transfer:
        pending.pop(name, None)
        token = match[2]
    else:
        # Keep a generated identity stable across container restarts.
        token = state['identities'].get(name) or secrets.token_hex(16)
        if new_account:
            pending[name] = True

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
    card_paths, card_created = [], False
    if not transfer and pending.get(name, False):
        card_paths, card_created = prepare_memory_card(name, container=True)
        pending.pop(name, None)
        save_state(path, state)
    else:
        card_paths = existing_account_cards(name, generated_card_directory(container=True))
    print('Account accepted. Game login details:', flush=True)
    print(f'  Username: {name}', flush=True)
    print(f'  Password: {secret}', flush=True)
    print(f'  REO1 transfer code: REO1-{name}-{token}', flush=True)
    print('Use the username and password in the game. Save the REO1 code to import this account later.', flush=True)
    print('Keep these credentials and the container logs private.', flush=True)
    show_memory_cards(card_paths, card_created, lambda message: print(message, flush=True), container=True)


def main():
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        raise ValueError('Run the launcher as a regular user, without sudo.')
    if os.environ.get('OBWEB_RUN_MODE') == 'container':
        if os.environ.get('OBWEB_REO_CODE') and not os.environ.get('OBWEB_USERNAME'):
            raise ValueError('OBWEB_USERNAME is required when OBWEB_REO_CODE is set.')
        login_from_environment()
        return
    # All interactive credentials stay in the local terminal, not shell stdout/logs.
    output_device = 'CONOUT$' if os.name == 'nt' else '/dev/tty'
    input_device = 'CONIN$' if os.name == 'nt' else '/dev/tty'
    with open(output_device, 'w') as tty, open(input_device, 'r') as tty_input:
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
            preferences = state.setdefault('memory_cards', {})
            if mode in ('i', 'import'):
                while True:
                    answer = ask('Create memory cards for this imported account? [y/N]: ').lower()
                    if answer in ('', 'n', 'no', 'y', 'yes'):
                        preferences[name] = answer in ('y', 'yes')
                        break
                    say('Choose y or n.')
            elif mode in ('n', 'new'):
                preferences[name] = True
            save_state(path, state)
            card_paths, card_created = [], False
            if preferences.get(name, True):
                card_paths, card_created = prepare_memory_card(name)
            say('Account accepted. Game login details:')
            say(f'  Username: {name}')
            say(f'  Password: {secret}')
            say(f'  REO1 transfer code: REO1-{name}-{token}')
            say('Use the username and password in the game. Save the REO1 code to import this account later.')
            say('Keep these credentials private; do not share screenshots of this screen.')
            show_memory_cards(card_paths, card_created, say)
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
