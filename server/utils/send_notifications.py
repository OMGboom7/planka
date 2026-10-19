# Copyright (c) 2024 PLANKA Software GmbH
# Licensed under the Fair Use License: https://github.com/plankanban/planka/blob/master/LICENSE.md

import sys
import json
import logging
import hashlib
import os
import tempfile
import certifi
import apprise


BLOCKED_SCHEMAS_SET = {
    'syslog',
    'dbus',
    'kde',
    'qt',
    'glib',
    'gnome',
    'macosx',
    'windows',
}


def build_ca_bundle():
    custom_bundle = os.environ.get('REQUESTS_CA_BUNDLE')
    if not custom_bundle:
        return

    if not os.path.isfile(custom_bundle):
        print(f'[ca] CA bundle not found: {custom_bundle}', file=sys.stderr)
        os.environ.pop('REQUESTS_CA_BUNDLE', None)
        return

    try:
        with open(custom_bundle, 'rb') as custom_file:
            custom_data = custom_file.read()

        with open(certifi.where(), 'rb') as public_file:
            public_data = public_file.read()

        digest = hashlib.sha256(custom_data + public_data).hexdigest()[:16]
        merged_path = os.path.join(tempfile.gettempdir(), f'planka-ca-{digest}.pem')

        if not os.path.exists(merged_path):
            temporary_path = f'{merged_path}.tmp'
            with open(temporary_path, 'wb') as merged_file:
                merged_file.write(custom_data)
                merged_file.write(b'\n')
                merged_file.write(public_data)
            os.replace(temporary_path, merged_path)

        os.environ['REQUESTS_CA_BUNDLE'] = merged_path
    except OSError as error:
        print(f'[ca] Failed to build CA bundle: {error}', file=sys.stderr)
        os.environ.pop('REQUESTS_CA_BUNDLE', None)


build_ca_bundle()


last_apprise_message = None
class CaptureWarningHandler(logging.Handler):
    def emit(self, record):
        global last_apprise_message
        last_apprise_message = record.getMessage()


capture_warning_handler = CaptureWarningHandler()
capture_warning_handler.setLevel(logging.WARNING)

apprise_logger = logging.getLogger('apprise')
apprise_logger.setLevel(logging.WARNING)
apprise_logger.propagate = False
apprise_logger.addHandler(capture_warning_handler)


def send_notification(url, title, body, body_format):
    app = apprise.Apprise()
    app.add(url)
    return app.notify(title=title, body=body, body_format=body_format)


if __name__ == '__main__':
    services = json.loads(sys.argv[1])
    title = sys.argv[2]
    body_by_format = json.loads(sys.argv[3])

    errors = []
    for service in services:
        url = service['url']
        schema = url.split(':')[0]

        if schema in BLOCKED_SCHEMAS_SET:
            errors.append(f'[{schema}] Blocked service schema')
            continue

        body_format = service['format']
        body = body_by_format[body_format]

        last_apprise_message = None
        if not send_notification(url, title, body, body_format):
            if last_apprise_message:
                if last_apprise_message == 'There are no service(s) to notify':
                    errors.append(f'[{schema}] Unknown service URL')
                else:
                    errors.append(f'[{schema}] {last_apprise_message}')
            else:
                errors.append(f'[{schema}] Unknown error')

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

        sys.exit(1)
