"""Account setup for the desktop UI; reuses the native identity and card format."""
import secrets

import login_web as login


def permission_message(action, path, error):
    """Describe local storage failures without exposing identity contents."""
    denied_path = error.filename or str(path)
    code = getattr(error, 'winerror', None) or error.errno
    suffix = f' (OS error {code})' if code is not None else ''
    return (f'Permission denied while {action}{suffix}.\n\n'
            f'Account file: {path}\nAccess denied to: {denied_path}\n\n'
            'This is a local file-access problem, not an invalid REO1 code. '
            'Check that your current user can read and write this folder and its account file. '
            'Files created under another user or an elevated session may have different permissions. '
            'Do not delete your saved identity or change permissions for the whole application.')


def load_accounts(path):
    try:
        return login.load_state(path)
    except PermissionError as error:
        raise ValueError(permission_message('reading saved accounts', path, error)) from None


def save_accounts(path, state):
    try:
        login.save_state(path, state)
    except PermissionError as error:
        raise ValueError(permission_message('saving the account', path, error)) from None


def create_saved_cards(name):
    """Generate cards for an existing local identity without re-registering it."""
    path = login.state_path()
    state = load_accounts(path)
    if not login.NAME.fullmatch(name) or name not in state['identities']:
        raise ValueError('Select a saved account before creating memory cards.')
    cards, _ = login.prepare_memory_card(name)
    state.setdefault('memory_cards', {})[name] = True
    save_accounts(path, state)
    return {'name': name, 'cards': [str(card) for card in cards]}


def prepare_account(mode, value, create_cards=None):
    path = login.state_path()
    state = load_accounts(path)
    if mode == 'import':
        match = login.TRANSFER.fullmatch(value.strip())
        if not match:
            raise ValueError('Paste the complete REO1 transfer code from Outbreak Web.')
        name, token = match.groups()
    elif mode in ('new', 'saved'):
        name = value.strip()
        if not login.NAME.fullmatch(name):
            raise ValueError('Use 1 to 15 letters and numbers for the username.')
        if mode == 'saved' and name not in state['identities']:
            raise ValueError('Select a saved account or import its REO1 code.')
        # Retain the token after an ambiguous request or a failed card export.
        token = state['identities'].get(name) or secrets.token_hex(16)
    else:
        raise ValueError('Choose a saved account, a new account or import.')
    state['identities'][name] = token
    save_accounts(path, state)
    password = login.credential(name, token)
    status = login.register(name, password)
    if status == 409:
        raise ValueError('Username already registered with another credential. Import the matching REO1 code or choose another username.')
    if not 200 <= status < 300:
        raise ValueError(f'Account service returned HTTP {status}. The bridge was not started.')
    preferences = state.setdefault('memory_cards', {})
    if mode == 'new':
        preferences[name] = True
    elif mode == 'import':
        preferences[name] = bool(create_cards)
    state['last_name'] = name
    save_accounts(path, state)
    if preferences.get(name, True):
        cards, _ = login.prepare_memory_card(name)
    else:
        cards = login.existing_account_cards(name, login.generated_card_directory())
    return {'name': name, 'password': password, 'code': f'REO1-{name}-{token}',
            'cards': [str(card) for card in cards]}
