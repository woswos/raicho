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
    'authentication_max_bytes',
    'control_max_bytes',
    'maximum_json_depth',
    'heartbeat_interval_ms',
    'heartbeat_timeout_ms',
    'maximum_active_connections',
    'maximum_pending_authentications',
    'maximum_queued_messages',
}


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


def validate_sources(schema, limits):
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
    if limits['authentication_max_bytes'] > limits['control_max_bytes']:
        raise ValueError('Authentication frames cannot exceed the control limit.')
    if limits['heartbeat_interval_ms'] >= limits['heartbeat_timeout_ms']:
        raise ValueError('Heartbeat timeout must exceed its interval.')
