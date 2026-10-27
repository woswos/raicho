// Generated from protocol/schema/status.schema.json.
var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) =>
  function __require() {
    try {
      return (mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports);
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

// status_validator_generated.js
var validate = validate10;
var status_validator_generated_default = validate10;
var schema12 = { type: 'string', enum: ['ready', 'unavailable'] };
var func0 = Object.prototype.hasOwnProperty;
var func58 = require_ucs2length().default;
var schema13 = {
  type: 'object',
  additionalProperties: false,
  required: ['status', 'engine', 'version'],
  properties: {
    status: { $ref: '#/definitions/Readiness' },
    engine: { type: 'string', enum: ['sqlite'] },
    version: { $ref: '#/definitions/Label' },
  },
};
var pattern0 = new RegExp('^[!-~]+$', 'u');
function validate11(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.status === void 0 || !func0.call(data, 'status')) && (missing0 = 'status')) ||
        ((data.engine === void 0 || !func0.call(data, 'engine')) && (missing0 = 'engine')) ||
        ((data.version === void 0 || !func0.call(data, 'version')) && (missing0 = 'version'))
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
          if (!(key0 === 'status' || key0 === 'engine' || key0 === 'version')) {
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
          if (data.status !== void 0 && func0.call(data, 'status')) {
            let data0 = data.status;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate11.errors = [
                {
                  instancePath: instancePath + '/status',
                  schemaPath: '#/definitions/Readiness/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'ready' || data0 === 'unavailable')) {
              validate11.errors = [
                {
                  instancePath: instancePath + '/status',
                  schemaPath: '#/definitions/Readiness/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema12.enum },
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
            if (data.engine !== void 0 && func0.call(data, 'engine')) {
              let data1 = data.engine;
              const _errs5 = errors;
              if (typeof data1 !== 'string') {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/engine',
                    schemaPath: '#/properties/engine/type',
                    keyword: 'type',
                    params: { type: 'string' },
                    message: 'must be string',
                  },
                ];
                return false;
              }
              if (!(data1 === 'sqlite')) {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/engine',
                    schemaPath: '#/properties/engine/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema13.properties.engine.enum },
                    message: 'must be equal to one of the allowed values',
                  },
                ];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.version !== void 0 && func0.call(data, 'version')) {
                let data2 = data.version;
                const _errs7 = errors;
                const _errs8 = errors;
                if (errors === _errs8) {
                  if (typeof data2 === 'string') {
                    if (func58(data2) > 80) {
                      validate11.errors = [
                        {
                          instancePath: instancePath + '/version',
                          schemaPath: '#/definitions/Label/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 80 },
                          message: 'must NOT have more than 80 characters',
                        },
                      ];
                      return false;
                    } else {
                      if (func58(data2) < 1) {
                        validate11.errors = [
                          {
                            instancePath: instancePath + '/version',
                            schemaPath: '#/definitions/Label/minLength',
                            keyword: 'minLength',
                            params: { limit: 1 },
                            message: 'must NOT have fewer than 1 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern0.test(data2)) {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/version',
                              schemaPath: '#/definitions/Label/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[!-~]+$' },
                              message: 'must match pattern "^[!-~]+$"',
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate11.errors = [
                      {
                        instancePath: instancePath + '/version',
                        schemaPath: '#/definitions/Label/type',
                        keyword: 'type',
                        params: { type: 'string' },
                        message: 'must be string',
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs7 === errors;
              } else {
                var valid0 = true;
              }
            }
          }
        }
      }
    } else {
      validate11.errors = [
        { instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' }, message: 'must be object' },
      ];
      return false;
    }
  }
  validate11.errors = vErrors;
  return errors === 0;
}
var schema16 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind', 'status', 'generation', 'last_error', 'heartbeat_count'],
  properties: {
    kind: { type: 'string', enum: ['thunderbird'] },
    status: { $ref: '#/definitions/BackendState' },
    generation: { oneOf: [{ $ref: '#/definitions/Generation' }, { $ref: '#/definitions/Nothing' }] },
    last_error: { oneOf: [{ $ref: '#/definitions/BackendError' }, { $ref: '#/definitions/Nothing' }] },
    heartbeat_count: { type: 'integer', minimum: 0, maximum: 9007199254740991 },
  },
};
var schema17 = { type: 'string', enum: ['unconfigured', 'disconnected', 'connected', 'revoked', 'unavailable'] };
var schema20 = {
  type: 'string',
  enum: [
    'authentication_failed',
    'authentication_timeout',
    'incompatible_version',
    'invalid_message',
    'message_too_large',
    'unexpected_message',
    'stale_generation',
    'heartbeat_timeout',
    'session_replaced',
    'disconnected',
    'storage_unavailable',
    'server_busy',
  ],
};
var pattern1 = new RegExp('^[a-f0-9]{32}$', 'u');
function validate13(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) ||
        ((data.status === void 0 || !func0.call(data, 'status')) && (missing0 = 'status')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.last_error === void 0 || !func0.call(data, 'last_error')) && (missing0 = 'last_error')) ||
        ((data.heartbeat_count === void 0 || !func0.call(data, 'heartbeat_count')) && (missing0 = 'heartbeat_count'))
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
            key0 === 'kind' ||
            key0 === 'status' ||
            key0 === 'generation' ||
            key0 === 'last_error' ||
            key0 === 'heartbeat_count'
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
          if (data.kind !== void 0 && func0.call(data, 'kind')) {
            let data0 = data.kind;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate13.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'thunderbird')) {
              validate13.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema16.properties.kind.enum },
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
            if (data.status !== void 0 && func0.call(data, 'status')) {
              let data1 = data.status;
              const _errs4 = errors;
              if (typeof data1 !== 'string') {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/status',
                    schemaPath: '#/definitions/BackendState/type',
                    keyword: 'type',
                    params: { type: 'string' },
                    message: 'must be string',
                  },
                ];
                return false;
              }
              if (!(
                data1 === 'unconfigured' ||
                data1 === 'disconnected' ||
                data1 === 'connected' ||
                data1 === 'revoked' ||
                data1 === 'unavailable'
              )) {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/status',
                    schemaPath: '#/definitions/BackendState/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema17.enum },
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
              if (data.generation !== void 0 && func0.call(data, 'generation')) {
                let data2 = data.generation;
                const _errs7 = errors;
                const _errs8 = errors;
                let valid2 = false;
                let passing0 = null;
                const _errs9 = errors;
                const _errs10 = errors;
                if (errors === _errs10) {
                  if (typeof data2 === 'string') {
                    if (func58(data2) > 32) {
                      const err0 = {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 32 },
                        message: 'must NOT have more than 32 characters',
                      };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func58(data2) < 32) {
                        const err1 = {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/minLength',
                          keyword: 'minLength',
                          params: { limit: 32 },
                          message: 'must NOT have fewer than 32 characters',
                        };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (!pattern1.test(data2)) {
                          const err2 = {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/pattern',
                            keyword: 'pattern',
                            params: { pattern: '^[a-f0-9]{32}$' },
                            message: 'must match pattern "^[a-f0-9]{32}$"',
                          };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                        }
                      }
                    }
                  } else {
                    const err3 = {
                      instancePath: instancePath + '/generation',
                      schemaPath: '#/definitions/Generation/type',
                      keyword: 'type',
                      params: { type: 'string' },
                      message: 'must be string',
                    };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                }
                var _valid0 = _errs9 === errors;
                if (_valid0) {
                  valid2 = true;
                  passing0 = 0;
                }
                const _errs12 = errors;
                if (data2 !== null) {
                  const err4 = {
                    instancePath: instancePath + '/generation',
                    schemaPath: '#/definitions/Nothing/type',
                    keyword: 'type',
                    params: { type: 'null' },
                    message: 'must be null',
                  };
                  if (vErrors === null) {
                    vErrors = [err4];
                  } else {
                    vErrors.push(err4);
                  }
                  errors++;
                }
                var _valid0 = _errs12 === errors;
                if (_valid0 && valid2) {
                  valid2 = false;
                  passing0 = [passing0, 1];
                } else {
                  if (_valid0) {
                    valid2 = true;
                    passing0 = 1;
                  }
                }
                if (!valid2) {
                  const err5 = {
                    instancePath: instancePath + '/generation',
                    schemaPath: '#/properties/generation/oneOf',
                    keyword: 'oneOf',
                    params: { passingSchemas: passing0 },
                    message: 'must match exactly one schema in oneOf',
                  };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate13.errors = vErrors;
                  return false;
                } else {
                  errors = _errs8;
                  if (vErrors !== null) {
                    if (_errs8) {
                      vErrors.length = _errs8;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs7 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.last_error !== void 0 && func0.call(data, 'last_error')) {
                  let data3 = data.last_error;
                  const _errs15 = errors;
                  const _errs16 = errors;
                  let valid5 = false;
                  let passing1 = null;
                  const _errs17 = errors;
                  if (typeof data3 !== 'string') {
                    const err6 = {
                      instancePath: instancePath + '/last_error',
                      schemaPath: '#/definitions/BackendError/type',
                      keyword: 'type',
                      params: { type: 'string' },
                      message: 'must be string',
                    };
                    if (vErrors === null) {
                      vErrors = [err6];
                    } else {
                      vErrors.push(err6);
                    }
                    errors++;
                  }
                  if (!(
                    data3 === 'authentication_failed' ||
                    data3 === 'authentication_timeout' ||
                    data3 === 'incompatible_version' ||
                    data3 === 'invalid_message' ||
                    data3 === 'message_too_large' ||
                    data3 === 'unexpected_message' ||
                    data3 === 'stale_generation' ||
                    data3 === 'heartbeat_timeout' ||
                    data3 === 'session_replaced' ||
                    data3 === 'disconnected' ||
                    data3 === 'storage_unavailable' ||
                    data3 === 'server_busy'
                  )) {
                    const err7 = {
                      instancePath: instancePath + '/last_error',
                      schemaPath: '#/definitions/BackendError/enum',
                      keyword: 'enum',
                      params: { allowedValues: schema20.enum },
                      message: 'must be equal to one of the allowed values',
                    };
                    if (vErrors === null) {
                      vErrors = [err7];
                    } else {
                      vErrors.push(err7);
                    }
                    errors++;
                  }
                  var _valid1 = _errs17 === errors;
                  if (_valid1) {
                    valid5 = true;
                    passing1 = 0;
                  }
                  const _errs20 = errors;
                  if (data3 !== null) {
                    const err8 = {
                      instancePath: instancePath + '/last_error',
                      schemaPath: '#/definitions/Nothing/type',
                      keyword: 'type',
                      params: { type: 'null' },
                      message: 'must be null',
                    };
                    if (vErrors === null) {
                      vErrors = [err8];
                    } else {
                      vErrors.push(err8);
                    }
                    errors++;
                  }
                  var _valid1 = _errs20 === errors;
                  if (_valid1 && valid5) {
                    valid5 = false;
                    passing1 = [passing1, 1];
                  } else {
                    if (_valid1) {
                      valid5 = true;
                      passing1 = 1;
                    }
                  }
                  if (!valid5) {
                    const err9 = {
                      instancePath: instancePath + '/last_error',
                      schemaPath: '#/properties/last_error/oneOf',
                      keyword: 'oneOf',
                      params: { passingSchemas: passing1 },
                      message: 'must match exactly one schema in oneOf',
                    };
                    if (vErrors === null) {
                      vErrors = [err9];
                    } else {
                      vErrors.push(err9);
                    }
                    errors++;
                    validate13.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs16;
                    if (vErrors !== null) {
                      if (_errs16) {
                        vErrors.length = _errs16;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs15 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.heartbeat_count !== void 0 && func0.call(data, 'heartbeat_count')) {
                    let data4 = data.heartbeat_count;
                    const _errs23 = errors;
                    if (!(typeof data4 == 'number' && !(data4 % 1) && !isNaN(data4) && isFinite(data4))) {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/heartbeat_count',
                          schemaPath: '#/properties/heartbeat_count/type',
                          keyword: 'type',
                          params: { type: 'integer' },
                          message: 'must be integer',
                        },
                      ];
                      return false;
                    }
                    if (errors === _errs23) {
                      if (typeof data4 == 'number' && isFinite(data4)) {
                        if (data4 > 9007199254740991 || isNaN(data4)) {
                          validate13.errors = [
                            {
                              instancePath: instancePath + '/heartbeat_count',
                              schemaPath: '#/properties/heartbeat_count/maximum',
                              keyword: 'maximum',
                              params: { comparison: '<=', limit: 9007199254740991 },
                              message: 'must be <= 9007199254740991',
                            },
                          ];
                          return false;
                        } else {
                          if (data4 < 0 || isNaN(data4)) {
                            validate13.errors = [
                              {
                                instancePath: instancePath + '/heartbeat_count',
                                schemaPath: '#/properties/heartbeat_count/minimum',
                                keyword: 'minimum',
                                params: { comparison: '>=', limit: 0 },
                                message: 'must be >= 0',
                              },
                            ];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs23 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate13.errors = [
        { instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' }, message: 'must be object' },
      ];
      return false;
    }
  }
  validate13.errors = vErrors;
  return errors === 0;
}
function validate10(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.status === void 0 || !func0.call(data, 'status')) && (missing0 = 'status')) ||
        ((data.database === void 0 || !func0.call(data, 'database')) && (missing0 = 'database')) ||
        ((data.backend === void 0 || !func0.call(data, 'backend')) && (missing0 = 'backend')) ||
        ((data.version === void 0 || !func0.call(data, 'version')) && (missing0 = 'version')) ||
        ((data.commit === void 0 || !func0.call(data, 'commit')) && (missing0 = 'commit'))
      ) {
        validate10.errors = [
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
            key0 === 'status' ||
            key0 === 'database' ||
            key0 === 'backend' ||
            key0 === 'version' ||
            key0 === 'commit'
          )) {
            validate10.errors = [
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
          if (data.status !== void 0 && func0.call(data, 'status')) {
            let data0 = data.status;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate10.errors = [
                {
                  instancePath: instancePath + '/status',
                  schemaPath: '#/definitions/Readiness/type',
                  keyword: 'type',
                  params: { type: 'string' },
                  message: 'must be string',
                },
              ];
              return false;
            }
            if (!(data0 === 'ready' || data0 === 'unavailable')) {
              validate10.errors = [
                {
                  instancePath: instancePath + '/status',
                  schemaPath: '#/definitions/Readiness/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema12.enum },
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
            if (data.database !== void 0 && func0.call(data, 'database')) {
              const _errs5 = errors;
              if (
                !validate11(data.database, {
                  instancePath: instancePath + '/database',
                  parentData: data,
                  parentDataProperty: 'database',
                  rootData,
                })
              ) {
                vErrors = vErrors === null ? validate11.errors : vErrors.concat(validate11.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.backend !== void 0 && func0.call(data, 'backend')) {
                const _errs6 = errors;
                if (
                  !validate13(data.backend, {
                    instancePath: instancePath + '/backend',
                    parentData: data,
                    parentDataProperty: 'backend',
                    rootData,
                  })
                ) {
                  vErrors = vErrors === null ? validate13.errors : vErrors.concat(validate13.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0 && func0.call(data, 'version')) {
                  let data3 = data.version;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === 'string') {
                      if (func58(data3) > 80) {
                        validate10.errors = [
                          {
                            instancePath: instancePath + '/version',
                            schemaPath: '#/definitions/Label/maxLength',
                            keyword: 'maxLength',
                            params: { limit: 80 },
                            message: 'must NOT have more than 80 characters',
                          },
                        ];
                        return false;
                      } else {
                        if (func58(data3) < 1) {
                          validate10.errors = [
                            {
                              instancePath: instancePath + '/version',
                              schemaPath: '#/definitions/Label/minLength',
                              keyword: 'minLength',
                              params: { limit: 1 },
                              message: 'must NOT have fewer than 1 characters',
                            },
                          ];
                          return false;
                        } else {
                          if (!pattern0.test(data3)) {
                            validate10.errors = [
                              {
                                instancePath: instancePath + '/version',
                                schemaPath: '#/definitions/Label/pattern',
                                keyword: 'pattern',
                                params: { pattern: '^[!-~]+$' },
                                message: 'must match pattern "^[!-~]+$"',
                              },
                            ];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate10.errors = [
                        {
                          instancePath: instancePath + '/version',
                          schemaPath: '#/definitions/Label/type',
                          keyword: 'type',
                          params: { type: 'string' },
                          message: 'must be string',
                        },
                      ];
                      return false;
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.commit !== void 0 && func0.call(data, 'commit')) {
                    let data4 = data.commit;
                    const _errs10 = errors;
                    const _errs11 = errors;
                    if (errors === _errs11) {
                      if (typeof data4 === 'string') {
                        if (func58(data4) > 80) {
                          validate10.errors = [
                            {
                              instancePath: instancePath + '/commit',
                              schemaPath: '#/definitions/Label/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 80 },
                              message: 'must NOT have more than 80 characters',
                            },
                          ];
                          return false;
                        } else {
                          if (func58(data4) < 1) {
                            validate10.errors = [
                              {
                                instancePath: instancePath + '/commit',
                                schemaPath: '#/definitions/Label/minLength',
                                keyword: 'minLength',
                                params: { limit: 1 },
                                message: 'must NOT have fewer than 1 characters',
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data4)) {
                              validate10.errors = [
                                {
                                  instancePath: instancePath + '/commit',
                                  schemaPath: '#/definitions/Label/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[!-~]+$' },
                                  message: 'must match pattern "^[!-~]+$"',
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate10.errors = [
                          {
                            instancePath: instancePath + '/commit',
                            schemaPath: '#/definitions/Label/type',
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
                }
              }
            }
          }
        }
      }
    } else {
      validate10.errors = [
        { instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' }, message: 'must be object' },
      ];
      return false;
    }
  }
  validate10.errors = vErrors;
  return errors === 0;
}
export { status_validator_generated_default as default, validate };
