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


def validate_schema(schema, definitions):
    if not isinstance(schema, dict) or set(schema) - VOCABULARY:
        raise ValueError('Unsupported protocol schema vocabulary.')
    reference = schema.get('$ref')
    if reference is not None:
        prefix = '#/definitions/'
        if (
            not isinstance(reference, str)
            or not reference.startswith(prefix)
            or reference[len(prefix) :] not in definitions
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
        raise ValueError(
            'Diagnostics must list backend states, errors, and contract errors.'
        )
    for codes in diagnostics.values():
        if (
            not isinstance(codes, list)
            or not codes
            or len(set(codes)) != len(codes)
            or not all(
                isinstance(code, str) and DIAGNOSTIC_CODE.fullmatch(code)
                for code in codes
            )
        ):
            raise ValueError('Diagnostic codes must be unique snake_case words.')
    protocol_errors = set(
        schema['definitions']['ProtocolError']['properties']['code']['enum']
    )
    if not protocol_errors <= set(diagnostics['backend_errors']):
        raise ValueError('Every protocol error code must be a backend error.')
    if not set(diagnostics['contract_errors']) <= protocol_errors:
        raise ValueError('Every contract error must be a protocol error code.')


def validate_sources(schema, limits, diagnostics):
    if schema.get('$schema') != 'http://json-schema.org/draft-07/schema#':
        raise ValueError('The protocol uses JSON Schema draft 7.')
    definitions = schema.get('definitions', {})
    validate_schema(schema, definitions)
    if set(limits) != LIMIT_NAMES or any(
        type(value) is not int or not 0 < value <= 2147483647
        for value in limits.values()
    ):
        raise ValueError('Protocol limits must contain the expected positive integers.')
    for definition in definitions.values():
        properties = definition.get('properties', {})
        for name in [
            'protocol_version',
            'heartbeat_interval_ms',
            'heartbeat_timeout_ms',
        ]:
            if name in properties and properties[name].get('enum') != [limits[name]]:
                raise ValueError(f'Protocol schema disagrees with limit {name}.')
    if limits['maximum_authentication_bytes'] > limits['maximum_control_bytes']:
        raise ValueError('Authentication frames cannot exceed the control limit.')
    if limits['heartbeat_interval_ms'] >= limits['heartbeat_timeout_ms']:
        raise ValueError('Heartbeat timeout must exceed its interval.')
    validate_diagnostics(diagnostics, schema)
