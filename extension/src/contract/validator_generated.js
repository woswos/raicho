// Generated from protocol/schema/connector.schema.json.
var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) =>
  function __require() {
    try {
      return (
        mod ||
          (0, cb[__getOwnPropNames(cb)[0]])(
            (mod = { exports: {} }).exports,
            mod,
          ),
        mod.exports
      );
    } catch (e) {
      throw ((mod = 0), e);
    }
  };

// node_modules/ajv/dist/runtime/ucs2length.js
var require_ucs2length = __commonJS({
  'node_modules/ajv/dist/runtime/ucs2length.js'(exports) {
    'use strict';
    Object.defineProperty(exports, '__esModule', { value: true });
    function ucs2length(str) {
      const len = str.length;
      let length = 0;
      let pos = 0;
      let value;
      while (pos < len) {
        length++;
        value = str.charCodeAt(pos++);
        if (value >= 55296 && value <= 56319 && pos < len) {
          value = str.charCodeAt(pos);
          if ((value & 64512) === 56320) pos++;
        }
      }
      return length;
    }
    exports.default = ucs2length;
    ucs2length.code = 'require("ajv/dist/runtime/ucs2length").default';
  },
});

// validator_generated.js
var validate = validate10;
var validator_generated_default = validate10;
var schema12 = {
  type: 'object',
  additionalProperties: false,
  required: [
    'type',
    'protocol_version',
    'token',
    'backend_kind',
    'backend_version',
    'connector_version',
    'capabilities',
  ],
  properties: {
    type: { type: 'string', enum: ['authenticate'] },
    protocol_version: { type: 'integer', enum: [1] },
    token: {
      type: 'string',
      minLength: 64,
      maxLength: 64,
      pattern: '^[a-f0-9]{64}$',
    },
    backend_kind: {
      type: 'string',
      minLength: 1,
      maxLength: 32,
      pattern: '^[a-z][a-z0-9_]*$',
    },
    backend_version: {
      type: 'string',
      minLength: 1,
      maxLength: 64,
      pattern: '^[ -~]+$',
    },
    connector_version: {
      type: 'string',
      minLength: 1,
      maxLength: 64,
      pattern: '^[ -~]+$',
    },
    capabilities: { $ref: '#/definitions/Capabilities' },
  },
};
var func0 = Object.prototype.hasOwnProperty;
var func55 = require_ucs2length().default;
var pattern0 = new RegExp('^[a-f0-9]{64}$', 'u');
var pattern1 = new RegExp('^[a-z][a-z0-9_]*$', 'u');
var pattern2 = new RegExp('^[ -~]+$', 'u');
function validate11(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) &&
          (missing0 = 'type')) ||
        ((data.protocol_version === void 0 ||
          !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.token === void 0 || !func0.call(data, 'token')) &&
          (missing0 = 'token')) ||
        ((data.backend_kind === void 0 || !func0.call(data, 'backend_kind')) &&
          (missing0 = 'backend_kind')) ||
        ((data.backend_version === void 0 ||
          !func0.call(data, 'backend_version')) &&
          (missing0 = 'backend_version')) ||
        ((data.connector_version === void 0 ||
          !func0.call(data, 'connector_version')) &&
          (missing0 = 'connector_version')) ||
        ((data.capabilities === void 0 || !func0.call(data, 'capabilities')) &&
          (missing0 = 'capabilities'))
      ) {
        validate11.errors = [
          {
            instancePath,
            schemaPath: '#/required',
            keyword: 'required',
            params: { missingProperty: missing0 },
            message: "must have required property '" + missing0 + "'",
          },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'token' ||
            key0 === 'backend_kind' ||
            key0 === 'backend_version' ||
            key0 === 'connector_version' ||
            key0 === 'capabilities'
          )) {
            validate11.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
                message: 'must NOT have additional properties',
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.type !== void 0 && func0.call(data, 'type')) {
            let data0 = data.type;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate11.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'authenticate')) {
              validate11.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema12.properties.type.enum },
                  message: 'must be equal to one of the allowed values',
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (
              data.protocol_version !== void 0 &&
              func0.call(data, 'protocol_version')
            ) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(
                typeof data1 == 'number' &&
                !(data1 % 1) &&
                !isNaN(data1) &&
                isFinite(data1)
              )) {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                    message: 'must be integer',
                  },
                ];
                return false;
              }
              if (!(data1 === 1)) {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: {
                      allowedValues: schema12.properties.protocol_version.enum,
                    },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.token !== void 0 && func0.call(data, 'token')) {
                let data2 = data.token;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (typeof data2 === 'string') {
                    if (func55(data2) > 64) {
                      validate11.errors = [
                        {
                          instancePath: instancePath + '/token',
                          schemaPath: '#/properties/token/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 64 },
                          message: 'must NOT have more than 64 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 64) {
                        validate11.errors = [
                          {
                            instancePath: instancePath + '/token',
                            schemaPath: '#/properties/token/minLength',
                            keyword: 'minLength',
                            params: { limit: 64 },
                            message: 'must NOT have fewer than 64 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern0.test(data2)) {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/token',
                              schemaPath: '#/properties/token/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{64}$' },
                              message: 'must match pattern "^[a-f0-9]{64}$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate11.errors = [
                      {
                        instancePath: instancePath + '/token',
                        schemaPath: '#/properties/token/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (
                  data.backend_kind !== void 0 &&
                  func0.call(data, 'backend_kind')
                ) {
                  let data3 = data.backend_kind;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === 'string') {
                      if (func55(data3) > 32) {
                        validate11.errors = [
                          {
                            instancePath: instancePath + '/backend_kind',
                            schemaPath: '#/properties/backend_kind/maxLength',
                            keyword: 'maxLength',
                            params: { limit: 32 },
                            message: 'must NOT have more than 32 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (func55(data3) < 1) {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/backend_kind',
                              schemaPath: '#/properties/backend_kind/minLength',
                              keyword: 'minLength',
                              params: { limit: 1 },
                              message: 'must NOT have fewer than 1 characters',
                            },
                          ];
                          return false;
                        } else {
                          if (!pattern1.test(data3)) {
                            validate11.errors = [
                              {
                                instancePath: instancePath + '/backend_kind',
                                schemaPath: '#/properties/backend_kind/pattern',
                                keyword: 'pattern',
                                params: { pattern: '^[a-z][a-z0-9_]*$' },
                                message:
                                  'must match pattern "^[a-z][a-z0-9_]*$"',
                              },
                            ];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate11.errors = [
                        {
                          instancePath: instancePath + '/backend_kind',
                          schemaPath: '#/properties/backend_kind/type',
                          keyword: 'type',
                          params: { type: 'string' },
                          message: 'must be string',
                        },
                      ];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (
                    data.backend_version !== void 0 &&
                    func0.call(data, 'backend_version')
                  ) {
                    let data4 = data.backend_version;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (typeof data4 === 'string') {
                        if (func55(data4) > 64) {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/backend_version',
                              schemaPath:
                                '#/properties/backend_version/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                              message: 'must NOT have more than 64 characters',
                            },
                          ];
                          return false;
                        } else {
                          if (func55(data4) < 1) {
                            validate11.errors = [
                              {
                                instancePath: instancePath + '/backend_version',
                                schemaPath:
                                  '#/properties/backend_version/minLength',
                                keyword: 'minLength',
                                params: { limit: 1 },
                                message:
                                  'must NOT have fewer than 1 characters',
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern2.test(data4)) {
                              validate11.errors = [
                                {
                                  instancePath:
                                    instancePath + '/backend_version',
                                  schemaPath:
                                    '#/properties/backend_version/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[ -~]+$' },
                                  message: 'must match pattern "^[ -~]+$"',
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate11.errors = [
                          {
                            instancePath: instancePath + '/backend_version',
                            schemaPath: '#/properties/backend_version/type',
                            keyword: 'type',
                            params: { type: 'string' },
                            message: 'must be string',
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (
                      data.connector_version !== void 0 &&
                      func0.call(data, 'connector_version')
                    ) {
                      let data5 = data.connector_version;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (typeof data5 === 'string') {
                          if (func55(data5) > 64) {
                            validate11.errors = [
                              {
                                instancePath:
                                  instancePath + '/connector_version',
                                schemaPath:
                                  '#/properties/connector_version/maxLength',
                                keyword: 'maxLength',
                                params: { limit: 64 },
                                message:
                                  'must NOT have more than 64 characters',
                              },
                            ];
                            return false;
                          } else {
                            if (func55(data5) < 1) {
                              validate11.errors = [
                                {
                                  instancePath:
                                    instancePath + '/connector_version',
                                  schemaPath:
                                    '#/properties/connector_version/minLength',
                                  keyword: 'minLength',
                                  params: { limit: 1 },
                                  message:
                                    'must NOT have fewer than 1 characters',
                                },
                              ];
                              return false;
                            } else {
                              if (!pattern2.test(data5)) {
                                validate11.errors = [
                                  {
                                    instancePath:
                                      instancePath + '/connector_version',
                                    schemaPath:
                                      '#/properties/connector_version/pattern',
                                    keyword: 'pattern',
                                    params: { pattern: '^[ -~]+$' },
                                    message: 'must match pattern "^[ -~]+$"',
                                  },
                                ];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/connector_version',
                              schemaPath: '#/properties/connector_version/type',
                              keyword: 'type',
                              params: { type: 'string' },
                              message: 'must be string',
                            },
                          ];
                          return false;
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (
                        data.capabilities !== void 0 &&
                        func0.call(data, 'capabilities')
                      ) {
                        let data6 = data.capabilities;
                        const _errs14 = errors;
                        const _errs15 = errors;
                        if (errors === _errs15) {
                          if (Array.isArray(data6)) {
                            if (data6.length > 0) {
                              validate11.errors = [
                                {
                                  instancePath: instancePath + '/capabilities',
                                  schemaPath:
                                    '#/definitions/Capabilities/maxItems',
                                  keyword: 'maxItems',
                                  params: { limit: 0 },
                                  message: 'must NOT have more than 0 items',
                                },
                              ];
                              return false;
                            } else {
                              var valid2 = true;
                              const len0 = data6.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs17 = errors;
                                if (typeof data6[i0] !== 'string') {
                                  validate11.errors = [
                                    {
                                      instancePath:
                                        instancePath + '/capabilities/' + i0,
                                      schemaPath:
                                        '#/definitions/Capabilities/items/type',
                                      keyword: 'type',
                                      params: { type: 'string' },
                                      message: 'must be string',
                                    },
                                  ];
                                  return false;
                                }
                                var valid2 = _errs17 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                              if (valid2) {
                                let i1 = data6.length;
                                let j0;
                                if (i1 > 1) {
                                  const indices0 = {};
                                  for (; i1--;) {
                                    let item0 = data6[i1];
                                    if (typeof item0 !== 'string') {
                                      continue;
                                    }
                                    if (typeof indices0[item0] == 'number') {
                                      j0 = indices0[item0];
                                      validate11.errors = [
                                        {
                                          instancePath:
                                            instancePath + '/capabilities',
                                          schemaPath:
                                            '#/definitions/Capabilities/uniqueItems',
                                          keyword: 'uniqueItems',
                                          params: { i: i1, j: j0 },
                                          message:
                                            'must NOT have duplicate items (items ## ' +
                                            j0 +
                                            ' and ' +
                                            i1 +
                                            ' are identical)',
                                        },
                                      ];
                                      return false;
                                      break;
                                    }
                                    indices0[item0] = i1;
                                  }
                                }
                              }
                            }
                          } else {
                            validate11.errors = [
                              {
                                instancePath: instancePath + '/capabilities',
                                schemaPath: '#/definitions/Capabilities/type',
                                keyword: 'type',
                                params: { type: 'array' },
                                message: 'must be array',
                              },
                            ];
                            return false;
                          }
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate11.errors = [
        {
          instancePath,
          schemaPath: '#/type',
          keyword: 'type',
          params: { type: 'object' },
          message: 'must be object',
        },
      ];
      return false;
    }
  }
  validate11.errors = vErrors;
  return errors === 0;
}
var schema14 = {
  type: 'object',
  additionalProperties: false,
  required: [
    'type',
    'protocol_version',
    'generation',
    'capabilities',
    'heartbeat_interval_ms',
    'heartbeat_timeout_ms',
  ],
  properties: {
    type: { type: 'string', enum: ['welcome'] },
    protocol_version: { type: 'integer', enum: [1] },
    generation: { $ref: '#/definitions/Generation' },
    capabilities: { $ref: '#/definitions/Capabilities' },
    heartbeat_interval_ms: { type: 'integer', enum: [15e3] },
    heartbeat_timeout_ms: { type: 'integer', enum: [45e3] },
  },
};
var pattern4 = new RegExp('^[a-f0-9]{32}$', 'u');
function validate13(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) &&
          (missing0 = 'type')) ||
        ((data.protocol_version === void 0 ||
          !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) &&
          (missing0 = 'generation')) ||
        ((data.capabilities === void 0 || !func0.call(data, 'capabilities')) &&
          (missing0 = 'capabilities')) ||
        ((data.heartbeat_interval_ms === void 0 ||
          !func0.call(data, 'heartbeat_interval_ms')) &&
          (missing0 = 'heartbeat_interval_ms')) ||
        ((data.heartbeat_timeout_ms === void 0 ||
          !func0.call(data, 'heartbeat_timeout_ms')) &&
          (missing0 = 'heartbeat_timeout_ms'))
      ) {
        validate13.errors = [
          {
            instancePath,
            schemaPath: '#/required',
            keyword: 'required',
            params: { missingProperty: missing0 },
            message: "must have required property '" + missing0 + "'",
          },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'capabilities' ||
            key0 === 'heartbeat_interval_ms' ||
            key0 === 'heartbeat_timeout_ms'
          )) {
            validate13.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
                message: 'must NOT have additional properties',
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.type !== void 0 && func0.call(data, 'type')) {
            let data0 = data.type;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate13.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'welcome')) {
              validate13.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema14.properties.type.enum },
                  message: 'must be equal to one of the allowed values',
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (
              data.protocol_version !== void 0 &&
              func0.call(data, 'protocol_version')
            ) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(
                typeof data1 == 'number' &&
                !(data1 % 1) &&
                !isNaN(data1) &&
                isFinite(data1)
              )) {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                    message: 'must be integer',
                  },
                ];
                return false;
              }
              if (!(data1 === 1)) {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: {
                      allowedValues: schema14.properties.protocol_version.enum,
                    },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (
                data.generation !== void 0 &&
                func0.call(data, 'generation')
              ) {
                let data2 = data.generation;
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func55(data2) > 32) {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                          message: 'must NOT have more than 32 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 32) {
                        validate13.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                            message: 'must NOT have fewer than 32 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern4.test(data2)) {
                          validate13.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                              message: 'must match pattern "^[a-f0-9]{32}$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate13.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (
                  data.capabilities !== void 0 &&
                  func0.call(data, 'capabilities')
                ) {
                  let data3 = data.capabilities;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (Array.isArray(data3)) {
                      if (data3.length > 0) {
                        validate13.errors = [
                          {
                            instancePath: instancePath + '/capabilities',
                            schemaPath: '#/definitions/Capabilities/maxItems',
                            keyword: 'maxItems',
                            params: { limit: 0 },
                            message: 'must NOT have more than 0 items',
                          },
                        ];
                        return false;
                      } else {
                        var valid3 = true;
                        const len0 = data3.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs12 = errors;
                          if (typeof data3[i0] !== 'string') {
                            validate13.errors = [
                              {
                                instancePath:
                                  instancePath + '/capabilities/' + i0,
                                schemaPath:
                                  '#/definitions/Capabilities/items/type',
                                keyword: 'type',
                                params: { type: 'string' },
                                message: 'must be string',
                              },
                            ];
                            return false;
                          }
                          var valid3 = _errs12 === errors;
                          if (!valid3) {
                            break;
                          }
                        }
                        if (valid3) {
                          let i1 = data3.length;
                          let j0;
                          if (i1 > 1) {
                            const indices0 = {};
                            for (; i1--;) {
                              let item0 = data3[i1];
                              if (typeof item0 !== 'string') {
                                continue;
                              }
                              if (typeof indices0[item0] == 'number') {
                                j0 = indices0[item0];
                                validate13.errors = [
                                  {
                                    instancePath:
                                      instancePath + '/capabilities',
                                    schemaPath:
                                      '#/definitions/Capabilities/uniqueItems',
                                    keyword: 'uniqueItems',
                                    params: { i: i1, j: j0 },
                                    message:
                                      'must NOT have duplicate items (items ## ' +
                                      j0 +
                                      ' and ' +
                                      i1 +
                                      ' are identical)',
                                  },
                                ];
                                return false;
                                break;
                              }
                              indices0[item0] = i1;
                            }
                          }
                        }
                      }
                    } else {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/capabilities',
                          schemaPath: '#/definitions/Capabilities/type',
                          keyword: 'type',
                          params: { type: 'array' },
                          message: 'must be array',
                        },
                      ];
                      return false;
                    }
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (
                    data.heartbeat_interval_ms !== void 0 &&
                    func0.call(data, 'heartbeat_interval_ms')
                  ) {
                    let data5 = data.heartbeat_interval_ms;
                    const _errs14 = errors;
                    if (!(
                      typeof data5 == 'number' &&
                      !(data5 % 1) &&
                      !isNaN(data5) &&
                      isFinite(data5)
                    )) {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/heartbeat_interval_ms',
                          schemaPath: '#/properties/heartbeat_interval_ms/type',
                          keyword: 'type',
                          params: { type: 'integer' },
                          message: 'must be integer',
                        },
                      ];
                      return false;
                    }
                    if (!(data5 === 15e3)) {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/heartbeat_interval_ms',
                          schemaPath: '#/properties/heartbeat_interval_ms/enum',
                          keyword: 'enum',
                          params: {
                            allowedValues:
                              schema14.properties.heartbeat_interval_ms.enum,
                          },
                          message: 'must be equal to one of the allowed values',
                        },
                      ];
                      return false;
                    }
                    var valid0 = _errs14 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (
                      data.heartbeat_timeout_ms !== void 0 &&
                      func0.call(data, 'heartbeat_timeout_ms')
                    ) {
                      let data6 = data.heartbeat_timeout_ms;
                      const _errs16 = errors;
                      if (!(
                        typeof data6 == 'number' &&
                        !(data6 % 1) &&
                        !isNaN(data6) &&
                        isFinite(data6)
                      )) {
                        validate13.errors = [
                          {
                            instancePath:
                              instancePath + '/heartbeat_timeout_ms',
                            schemaPath:
                              '#/properties/heartbeat_timeout_ms/type',
                            keyword: 'type',
                            params: { type: 'integer' },
                            message: 'must be integer',
                          },
                        ];
                        return false;
                      }
                      if (!(data6 === 45e3)) {
                        validate13.errors = [
                          {
                            instancePath:
                              instancePath + '/heartbeat_timeout_ms',
                            schemaPath:
                              '#/properties/heartbeat_timeout_ms/enum',
                            keyword: 'enum',
                            params: {
                              allowedValues:
                                schema14.properties.heartbeat_timeout_ms.enum,
                            },
                            message:
                              'must be equal to one of the allowed values',
                          },
                        ];
                        return false;
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate13.errors = [
        {
          instancePath,
          schemaPath: '#/type',
          keyword: 'type',
          params: { type: 'object' },
          message: 'must be object',
        },
      ];
      return false;
    }
  }
  validate13.errors = vErrors;
  return errors === 0;
}
var schema17 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'sequence'],
  properties: {
    type: { type: 'string', enum: ['ping'] },
    protocol_version: { type: 'integer', enum: [1] },
    generation: { $ref: '#/definitions/Generation' },
    sequence: { type: 'integer', minimum: 1, maximum: 2147483647 },
  },
};
function validate15(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) &&
          (missing0 = 'type')) ||
        ((data.protocol_version === void 0 ||
          !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) &&
          (missing0 = 'generation')) ||
        ((data.sequence === void 0 || !func0.call(data, 'sequence')) &&
          (missing0 = 'sequence'))
      ) {
        validate15.errors = [
          {
            instancePath,
            schemaPath: '#/required',
            keyword: 'required',
            params: { missingProperty: missing0 },
            message: "must have required property '" + missing0 + "'",
          },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'sequence'
          )) {
            validate15.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
                message: 'must NOT have additional properties',
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.type !== void 0 && func0.call(data, 'type')) {
            let data0 = data.type;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate15.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'ping')) {
              validate15.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema17.properties.type.enum },
                  message: 'must be equal to one of the allowed values',
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (
              data.protocol_version !== void 0 &&
              func0.call(data, 'protocol_version')
            ) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(
                typeof data1 == 'number' &&
                !(data1 % 1) &&
                !isNaN(data1) &&
                isFinite(data1)
              )) {
                validate15.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                    message: 'must be integer',
                  },
                ];
                return false;
              }
              if (!(data1 === 1)) {
                validate15.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: {
                      allowedValues: schema17.properties.protocol_version.enum,
                    },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (
                data.generation !== void 0 &&
                func0.call(data, 'generation')
              ) {
                let data2 = data.generation;
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func55(data2) > 32) {
                      validate15.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                          message: 'must NOT have more than 32 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 32) {
                        validate15.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                            message: 'must NOT have fewer than 32 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern4.test(data2)) {
                          validate15.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                              message: 'must match pattern "^[a-f0-9]{32}$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate15.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.sequence !== void 0 && func0.call(data, 'sequence')) {
                  let data3 = data.sequence;
                  const _errs9 = errors;
                  if (!(
                    typeof data3 == 'number' &&
                    !(data3 % 1) &&
                    !isNaN(data3) &&
                    isFinite(data3)
                  )) {
                    validate15.errors = [
                      {
                        instancePath: instancePath + '/sequence',
                        schemaPath: '#/properties/sequence/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                        message: 'must be integer',
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs9) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate15.errors = [
                          {
                            instancePath: instancePath + '/sequence',
                            schemaPath: '#/properties/sequence/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                            message: 'must be <= 2147483647',
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate15.errors = [
                            {
                              instancePath: instancePath + '/sequence',
                              schemaPath: '#/properties/sequence/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
                              message: 'must be >= 1',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate15.errors = [
        {
          instancePath,
          schemaPath: '#/type',
          keyword: 'type',
          params: { type: 'object' },
          message: 'must be object',
        },
      ];
      return false;
    }
  }
  validate15.errors = vErrors;
  return errors === 0;
}
var schema19 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'sequence'],
  properties: {
    type: { type: 'string', enum: ['pong'] },
    protocol_version: { type: 'integer', enum: [1] },
    generation: { $ref: '#/definitions/Generation' },
    sequence: { type: 'integer', minimum: 1, maximum: 2147483647 },
  },
};
function validate17(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) &&
          (missing0 = 'type')) ||
        ((data.protocol_version === void 0 ||
          !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) &&
          (missing0 = 'generation')) ||
        ((data.sequence === void 0 || !func0.call(data, 'sequence')) &&
          (missing0 = 'sequence'))
      ) {
        validate17.errors = [
          {
            instancePath,
            schemaPath: '#/required',
            keyword: 'required',
            params: { missingProperty: missing0 },
            message: "must have required property '" + missing0 + "'",
          },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'sequence'
          )) {
            validate17.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
                message: 'must NOT have additional properties',
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.type !== void 0 && func0.call(data, 'type')) {
            let data0 = data.type;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate17.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'pong')) {
              validate17.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema19.properties.type.enum },
                  message: 'must be equal to one of the allowed values',
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (
              data.protocol_version !== void 0 &&
              func0.call(data, 'protocol_version')
            ) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(
                typeof data1 == 'number' &&
                !(data1 % 1) &&
                !isNaN(data1) &&
                isFinite(data1)
              )) {
                validate17.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                    message: 'must be integer',
                  },
                ];
                return false;
              }
              if (!(data1 === 1)) {
                validate17.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: {
                      allowedValues: schema19.properties.protocol_version.enum,
                    },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (
                data.generation !== void 0 &&
                func0.call(data, 'generation')
              ) {
                let data2 = data.generation;
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func55(data2) > 32) {
                      validate17.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                          message: 'must NOT have more than 32 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 32) {
                        validate17.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                            message: 'must NOT have fewer than 32 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern4.test(data2)) {
                          validate17.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                              message: 'must match pattern "^[a-f0-9]{32}$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate17.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.sequence !== void 0 && func0.call(data, 'sequence')) {
                  let data3 = data.sequence;
                  const _errs9 = errors;
                  if (!(
                    typeof data3 == 'number' &&
                    !(data3 % 1) &&
                    !isNaN(data3) &&
                    isFinite(data3)
                  )) {
                    validate17.errors = [
                      {
                        instancePath: instancePath + '/sequence',
                        schemaPath: '#/properties/sequence/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                        message: 'must be integer',
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs9) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate17.errors = [
                          {
                            instancePath: instancePath + '/sequence',
                            schemaPath: '#/properties/sequence/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                            message: 'must be <= 2147483647',
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate17.errors = [
                            {
                              instancePath: instancePath + '/sequence',
                              schemaPath: '#/properties/sequence/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
                              message: 'must be >= 1',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate17.errors = [
        {
          instancePath,
          schemaPath: '#/type',
          keyword: 'type',
          params: { type: 'object' },
          message: 'must be object',
        },
      ];
      return false;
    }
  }
  validate17.errors = vErrors;
  return errors === 0;
}
var schema21 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'code'],
  properties: {
    type: { type: 'string', enum: ['error'] },
    protocol_version: { type: 'integer', enum: [1] },
    generation: { $ref: '#/definitions/Generation' },
    code: {
      type: 'string',
      enum: [
        'authentication_failed',
        'incompatible_version',
        'invalid_message',
        'message_too_large',
        'unexpected_message',
        'stale_generation',
        'heartbeat_timeout',
        'session_replaced',
        'server_busy',
      ],
    },
  },
};
function validate19(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) &&
          (missing0 = 'type')) ||
        ((data.protocol_version === void 0 ||
          !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.code === void 0 || !func0.call(data, 'code')) &&
          (missing0 = 'code'))
      ) {
        validate19.errors = [
          {
            instancePath,
            schemaPath: '#/required',
            keyword: 'required',
            params: { missingProperty: missing0 },
            message: "must have required property '" + missing0 + "'",
          },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'code'
          )) {
            validate19.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
                message: 'must NOT have additional properties',
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.type !== void 0 && func0.call(data, 'type')) {
            let data0 = data.type;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate19.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'error')) {
              validate19.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema21.properties.type.enum },
                  message: 'must be equal to one of the allowed values',
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (
              data.protocol_version !== void 0 &&
              func0.call(data, 'protocol_version')
            ) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(
                typeof data1 == 'number' &&
                !(data1 % 1) &&
                !isNaN(data1) &&
                isFinite(data1)
              )) {
                validate19.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                    message: 'must be integer',
                  },
                ];
                return false;
              }
              if (!(data1 === 1)) {
                validate19.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: {
                      allowedValues: schema21.properties.protocol_version.enum,
                    },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (
                data.generation !== void 0 &&
                func0.call(data, 'generation')
              ) {
                let data2 = data.generation;
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func55(data2) > 32) {
                      validate19.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                          message: 'must NOT have more than 32 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 32) {
                        validate19.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                            message: 'must NOT have fewer than 32 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern4.test(data2)) {
                          validate19.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                              message: 'must match pattern "^[a-f0-9]{32}$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate19.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.code !== void 0 && func0.call(data, 'code')) {
                  let data3 = data.code;
                  const _errs9 = errors;
                  if (typeof data3 !== 'string') {
                    validate19.errors = [
                      {
                        instancePath: instancePath + '/code',
                        schemaPath: '#/properties/code/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                  if (!(
                    data3 === 'authentication_failed' ||
                    data3 === 'incompatible_version' ||
                    data3 === 'invalid_message' ||
                    data3 === 'message_too_large' ||
                    data3 === 'unexpected_message' ||
                    data3 === 'stale_generation' ||
                    data3 === 'heartbeat_timeout' ||
                    data3 === 'session_replaced' ||
                    data3 === 'server_busy'
                  )) {
                    validate19.errors = [
                      {
                        instancePath: instancePath + '/code',
                        schemaPath: '#/properties/code/enum',
                        keyword: 'enum',
                        params: {
                          allowedValues: schema21.properties.code.enum,
                        },
                        message: 'must be equal to one of the allowed values',
                      },
                    ];
                    return false;
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate19.errors = [
        {
          instancePath,
          schemaPath: '#/type',
          keyword: 'type',
          params: { type: 'object' },
          message: 'must be object',
        },
      ];
      return false;
    }
  }
  validate19.errors = vErrors;
  return errors === 0;
}
function validate10(
  data,
  { instancePath = '', parentData, parentDataProperty, rootData = data } = {},
) {
  let vErrors = null;
  let errors = 0;
  const _errs0 = errors;
  let valid0 = false;
  let passing0 = null;
  const _errs1 = errors;
  if (
    !validate11(data, {
      instancePath,
      parentData,
      parentDataProperty,
      rootData,
    })
  ) {
    vErrors =
      vErrors === null ? validate11.errors : vErrors.concat(validate11.errors);
    errors = vErrors.length;
  }
  var _valid0 = _errs1 === errors;
  if (_valid0) {
    valid0 = true;
    passing0 = 0;
  }
  const _errs2 = errors;
  if (
    !validate13(data, {
      instancePath,
      parentData,
      parentDataProperty,
      rootData,
    })
  ) {
    vErrors =
      vErrors === null ? validate13.errors : vErrors.concat(validate13.errors);
    errors = vErrors.length;
  }
  var _valid0 = _errs2 === errors;
  if (_valid0 && valid0) {
    valid0 = false;
    passing0 = [passing0, 1];
  } else {
    if (_valid0) {
      valid0 = true;
      passing0 = 1;
    }
    const _errs3 = errors;
    if (
      !validate15(data, {
        instancePath,
        parentData,
        parentDataProperty,
        rootData,
      })
    ) {
      vErrors =
        vErrors === null
          ? validate15.errors
          : vErrors.concat(validate15.errors);
      errors = vErrors.length;
    }
    var _valid0 = _errs3 === errors;
    if (_valid0 && valid0) {
      valid0 = false;
      passing0 = [passing0, 2];
    } else {
      if (_valid0) {
        valid0 = true;
        passing0 = 2;
      }
      const _errs4 = errors;
      if (
        !validate17(data, {
          instancePath,
          parentData,
          parentDataProperty,
          rootData,
        })
      ) {
        vErrors =
          vErrors === null
            ? validate17.errors
            : vErrors.concat(validate17.errors);
        errors = vErrors.length;
      }
      var _valid0 = _errs4 === errors;
      if (_valid0 && valid0) {
        valid0 = false;
        passing0 = [passing0, 3];
      } else {
        if (_valid0) {
          valid0 = true;
          passing0 = 3;
        }
        const _errs5 = errors;
        if (
          !validate19(data, {
            instancePath,
            parentData,
            parentDataProperty,
            rootData,
          })
        ) {
          vErrors =
            vErrors === null
              ? validate19.errors
              : vErrors.concat(validate19.errors);
          errors = vErrors.length;
        }
        var _valid0 = _errs5 === errors;
        if (_valid0 && valid0) {
          valid0 = false;
          passing0 = [passing0, 4];
        } else {
          if (_valid0) {
            valid0 = true;
            passing0 = 4;
          }
        }
      }
    }
  }
  if (!valid0) {
    const err0 = {
      instancePath,
      schemaPath: '#/oneOf',
      keyword: 'oneOf',
      params: { passingSchemas: passing0 },
      message: 'must match exactly one schema in oneOf',
    };
    if (vErrors === null) {
      vErrors = [err0];
    } else {
      vErrors.push(err0);
    }
    errors++;
    validate10.errors = vErrors;
    return false;
  } else {
    errors = _errs0;
    if (vErrors !== null) {
      if (_errs0) {
        vErrors.length = _errs0;
      } else {
        vErrors = null;
      }
    }
  }
  validate10.errors = vErrors;
  return errors === 0;
}
export { validator_generated_default as default, validate };
