import re

VOCABULARY = {
    '$schema',
    '$ref',
    'title',
    'definitions',
    'oneOf',
    'type',
    'properties',
    'required',
    'additionalProperties',
    'enum',
    'minLength',
    'maxLength',
    'pattern',
    'items',
    'maxItems',
    'uniqueItems',
    'minimum',
    'maximum',
}
LIMIT_NAMES = {
    'protocol_version',
    'authentication_deadline_ms',
    'maximum_authentication_bytes',
    'maximum_control_bytes',
    'maximum_json_depth',
    'maximum_wire_integer',
    'heartbeat_interval_ms',
    'heartbeat_timeout_ms',
    'maximum_active_connections',
    'maximum_pending_authentications',
    'authentication_failure_close_code',
    'protocol_failure_close_code',
    'session_replaced_close_code',
}
DIAGNOSTIC_LISTS = {'backend_states', 'backend_errors', 'contract_errors'}
DIAGNOSTIC_CODE = re.compile(r'[a-z]+(?:_[a-z]+)*')
DRAFT_7 = 'http://json-schema.org/draft-07/schema#'
MAXIMUM_JSON_DEPTH = 100
# The contract keeps wire integers in the signed 32-bit range.
MAXIMUM_WIRE_INTEGER = 2**31 - 1


def validate_schema(schema, definitions):
    if not isinstance(schema, dict) or set(schema) - VOCABULARY:
        raise ValueError('Unsupported protocol schema vocabulary.')
    reference = schema.get('$ref')
    if reference is not None:
        prefix = '#/definitions/'
        if (
            not isinstance(reference, str)
            or not reference.startswith(prefix)
            or reference.removeprefix(prefix) not in definitions
        ):
            raise ValueError('Protocol references must resolve to local definitions.')
    for name in ['properties', 'definitions']:
        for child in schema.get(name, {}).values():
            validate_schema(child, definitions)
    for child in schema.get('oneOf', []):
        validate_schema(child, definitions)
    if 'items' in schema:
        validate_schema(schema['items'], definitions)
    if isinstance(schema.get('additionalProperties'), dict):
        validate_schema(schema['additionalProperties'], definitions)


def validate_diagnostics(diagnostics, schema):
    if not isinstance(diagnostics, dict) or set(diagnostics) != DIAGNOSTIC_LISTS:
        raise ValueError('Diagnostics must list backend states, errors, and contract errors.')
    for codes in diagnostics.values():
        if (
            not isinstance(codes, list)
            or not codes
            or len(set(codes)) != len(codes)
            or not all(isinstance(code, str) and DIAGNOSTIC_CODE.fullmatch(code) for code in codes)
        ):
            raise ValueError('Diagnostic codes must be unique snake_case words.')
    protocol_errors = set(schema['definitions']['ProtocolError']['properties']['code']['enum'])
    if not protocol_errors <= set(diagnostics['backend_errors']):
        raise ValueError('Every protocol error code must be a backend error.')
    if not set(diagnostics['contract_errors']) <= protocol_errors:
        raise ValueError('Every contract error must be a protocol error code.')


def validate_document(schema):
    if schema.get('$schema') != DRAFT_7:
        raise ValueError('The protocol uses JSON Schema draft 7.')
    validate_schema(schema, schema.get('definitions', {}))


def validate_status(status, diagnostics):
    validate_document(status)
    definitions = status.get('definitions', {})
    for name, key in [
        ('BackendState', 'backend_states'),
        ('BackendError', 'backend_errors'),
    ]:
        if definitions.get(name, {}).get('enum') != diagnostics[key]:
            raise ValueError(f'Status schema disagrees with diagnostics {key}.')


def validate_sources(schema, limits, diagnostics):
    validate_document(schema)
    definitions = schema.get('definitions', {})
    if set(limits) != LIMIT_NAMES or any(type(value) is not int or value <= 0 for value in limits.values()):
        raise ValueError('Protocol limits must contain the expected positive integers.')
    if limits['maximum_wire_integer'] > MAXIMUM_WIRE_INTEGER:
        raise ValueError(f'maximum_wire_integer must not exceed {MAXIMUM_WIRE_INTEGER}.')
    if any(value > limits['maximum_wire_integer'] for value in limits.values()):
        raise ValueError('Protocol limits must not exceed maximum_wire_integer.')
    # serde_json stops parsing at depth 128, so a deeper limit would make the decoders disagree.
    if limits['maximum_json_depth'] > MAXIMUM_JSON_DEPTH:
        raise ValueError(f'maximum_json_depth must not exceed {MAXIMUM_JSON_DEPTH}.')
    for definition in definitions.values():
        properties = definition.get('properties', {})
        if 'protocol_version' in properties and properties['protocol_version'].get('enum') != [
            limits['protocol_version']
        ]:
            raise ValueError('Protocol schema disagrees with limit protocol_version.')
        if 'sequence' in properties and properties['sequence'].get('maximum') != limits['maximum_wire_integer']:
            raise ValueError('Protocol schema disagrees with limit maximum_wire_integer.')
    if limits['maximum_authentication_bytes'] > limits['maximum_control_bytes']:
        raise ValueError('Authentication frames cannot exceed the control limit.')
    if limits['heartbeat_interval_ms'] >= limits['heartbeat_timeout_ms']:
        raise ValueError('Heartbeat timeout must exceed its interval.')
    validate_diagnostics(diagnostics, schema)
