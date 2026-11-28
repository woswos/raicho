// Generated from protocol/schema/connector.schema.json.
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

// validator_generated.js
var validate = validate10;
var validator_generated_default = validate10;
var schema12 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'server_nonce'],
  properties: {
    type: { type: 'string', enum: ['challenge'] },
    protocol_version: { type: 'integer', enum: [2] },
    server_nonce: { $ref: '#/definitions/Nonce' },
  },
};
var func0 = Object.prototype.hasOwnProperty;
var func51 = require_ucs2length().default;
var pattern0 = new RegExp('^[a-f0-9]{64}$', 'u');
function validate11(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.server_nonce === void 0 || !func0.call(data, 'server_nonce')) && (missing0 = 'server_nonce'))
      ) {
        validate11.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'type' || key0 === 'protocol_version' || key0 === 'server_nonce')) {
            validate11.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
                },
              ];
              return false;
            }
            if (!(data0 === 'challenge')) {
              validate11.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema12.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate11.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema12.properties.protocol_version.enum },
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.server_nonce !== void 0 && func0.call(data, 'server_nonce')) {
                let data2 = data.server_nonce;
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 64) {
                      validate11.errors = [
                        {
                          instancePath: instancePath + '/server_nonce',
                          schemaPath: '#/definitions/Nonce/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 64 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 64) {
                        validate11.errors = [
                          {
                            instancePath: instancePath + '/server_nonce',
                            schemaPath: '#/definitions/Nonce/minLength',
                            keyword: 'minLength',
                            params: { limit: 64 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern0.test(data2)) {
                          validate11.errors = [
                            {
                              instancePath: instancePath + '/server_nonce',
                              schemaPath: '#/definitions/Nonce/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{64}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate11.errors = [
                      {
                        instancePath: instancePath + '/server_nonce',
                        schemaPath: '#/definitions/Nonce/type',
                        keyword: 'type',
                        params: { type: 'string' },
                      },
                    ];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
            }
          }
        }
      }
    } else {
      validate11.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
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
    'backend_kind',
    'backend_version',
    'connector_version',
    'capabilities',
    'client_nonce',
    'client_proof',
  ],
  properties: {
    type: { type: 'string', enum: ['authenticate'] },
    protocol_version: { type: 'integer', enum: [2] },
    backend_kind: { type: 'string', minLength: 1, maxLength: 32, pattern: '^[a-z][a-z0-9_]*$' },
    backend_version: { type: 'string', minLength: 1, maxLength: 64, pattern: '^[ -~]+$' },
    connector_version: { type: 'string', minLength: 1, maxLength: 64, pattern: '^[ -~]+$' },
    capabilities: { $ref: '#/definitions/Capabilities' },
    client_nonce: { $ref: '#/definitions/Nonce' },
    client_proof: { $ref: '#/definitions/Signature' },
  },
};
var pattern1 = new RegExp('^[a-z][a-z0-9_]*$', 'u');
var pattern2 = new RegExp('^[ -~]+$', 'u');
function validate13(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.backend_kind === void 0 || !func0.call(data, 'backend_kind')) && (missing0 = 'backend_kind')) ||
        ((data.backend_version === void 0 || !func0.call(data, 'backend_version')) && (missing0 = 'backend_version')) ||
        ((data.connector_version === void 0 || !func0.call(data, 'connector_version')) &&
          (missing0 = 'connector_version')) ||
        ((data.capabilities === void 0 || !func0.call(data, 'capabilities')) && (missing0 = 'capabilities')) ||
        ((data.client_nonce === void 0 || !func0.call(data, 'client_nonce')) && (missing0 = 'client_nonce')) ||
        ((data.client_proof === void 0 || !func0.call(data, 'client_proof')) && (missing0 = 'client_proof'))
      ) {
        validate13.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'backend_kind' ||
            key0 === 'backend_version' ||
            key0 === 'connector_version' ||
            key0 === 'capabilities' ||
            key0 === 'client_nonce' ||
            key0 === 'client_proof'
          )) {
            validate13.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
                },
              ];
              return false;
            }
            if (!(data0 === 'authenticate')) {
              validate13.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema14.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate13.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema14.properties.protocol_version.enum },
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.backend_kind !== void 0 && func0.call(data, 'backend_kind')) {
                let data2 = data.backend_kind;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/backend_kind',
                          schemaPath: '#/properties/backend_kind/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 1) {
                        validate13.errors = [
                          {
                            instancePath: instancePath + '/backend_kind',
                            schemaPath: '#/properties/backend_kind/minLength',
                            keyword: 'minLength',
                            params: { limit: 1 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern1.test(data2)) {
                          validate13.errors = [
                            {
                              instancePath: instancePath + '/backend_kind',
                              schemaPath: '#/properties/backend_kind/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-z][a-z0-9_]*$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate13.errors = [
                      {
                        instancePath: instancePath + '/backend_kind',
                        schemaPath: '#/properties/backend_kind/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.backend_version !== void 0 && func0.call(data, 'backend_version')) {
                  let data3 = data.backend_version;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === 'string') {
                      if (func51(data3) > 64) {
                        validate13.errors = [
                          {
                            instancePath: instancePath + '/backend_version',
                            schemaPath: '#/properties/backend_version/maxLength',
                            keyword: 'maxLength',
                            params: { limit: 64 },
                          },
                        ];
                        return false;
                      } else {
                        if (func51(data3) < 1) {
                          validate13.errors = [
                            {
                              instancePath: instancePath + '/backend_version',
                              schemaPath: '#/properties/backend_version/minLength',
                              keyword: 'minLength',
                              params: { limit: 1 },
                            },
                          ];
                          return false;
                        } else {
                          if (!pattern2.test(data3)) {
                            validate13.errors = [
                              {
                                instancePath: instancePath + '/backend_version',
                                schemaPath: '#/properties/backend_version/pattern',
                                keyword: 'pattern',
                                params: { pattern: '^[ -~]+$' },
                              },
                            ];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate13.errors = [
                        {
                          instancePath: instancePath + '/backend_version',
                          schemaPath: '#/properties/backend_version/type',
                          keyword: 'type',
                          params: { type: 'string' },
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
                  if (data.connector_version !== void 0 && func0.call(data, 'connector_version')) {
                    let data4 = data.connector_version;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 64) {
                          validate13.errors = [
                            {
                              instancePath: instancePath + '/connector_version',
                              schemaPath: '#/properties/connector_version/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 1) {
                            validate13.errors = [
                              {
                                instancePath: instancePath + '/connector_version',
                                schemaPath: '#/properties/connector_version/minLength',
                                keyword: 'minLength',
                                params: { limit: 1 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern2.test(data4)) {
                              validate13.errors = [
                                {
                                  instancePath: instancePath + '/connector_version',
                                  schemaPath: '#/properties/connector_version/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[ -~]+$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate13.errors = [
                          {
                            instancePath: instancePath + '/connector_version',
                            schemaPath: '#/properties/connector_version/type',
                            keyword: 'type',
                            params: { type: 'string' },
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
                    if (data.capabilities !== void 0 && func0.call(data, 'capabilities')) {
                      let data5 = data.capabilities;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      if (errors === _errs13) {
                        if (Array.isArray(data5)) {
                          if (data5.length > 0) {
                            validate13.errors = [
                              {
                                instancePath: instancePath + '/capabilities',
                                schemaPath: '#/definitions/Capabilities/maxItems',
                                keyword: 'maxItems',
                                params: { limit: 0 },
                              },
                            ];
                            return false;
                          } else {
                            var valid2 = true;
                            const len0 = data5.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs15 = errors;
                              if (typeof data5[i0] !== 'string') {
                                validate13.errors = [
                                  {
                                    instancePath: instancePath + '/capabilities/' + i0,
                                    schemaPath: '#/definitions/Capabilities/items/type',
                                    keyword: 'type',
                                    params: { type: 'string' },
                                  },
                                ];
                                return false;
                              }
                              var valid2 = _errs15 === errors;
                              if (!valid2) {
                                break;
                              }
                            }
                            if (valid2) {
                              let i1 = data5.length;
                              let j0;
                              if (i1 > 1) {
                                const indices0 = {};
                                for (; i1--;) {
                                  let item0 = data5[i1];
                                  if (typeof item0 !== 'string') {
                                    continue;
                                  }
                                  if (typeof indices0[item0] == 'number') {
                                    j0 = indices0[item0];
                                    validate13.errors = [
                                      {
                                        instancePath: instancePath + '/capabilities',
                                        schemaPath: '#/definitions/Capabilities/uniqueItems',
                                        keyword: 'uniqueItems',
                                        params: { i: i1, j: j0 },
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
                      if (data.client_nonce !== void 0 && func0.call(data, 'client_nonce')) {
                        let data7 = data.client_nonce;
                        const _errs17 = errors;
                        const _errs18 = errors;
                        if (errors === _errs18) {
                          if (typeof data7 === 'string') {
                            if (func51(data7) > 64) {
                              validate13.errors = [
                                {
                                  instancePath: instancePath + '/client_nonce',
                                  schemaPath: '#/definitions/Nonce/maxLength',
                                  keyword: 'maxLength',
                                  params: { limit: 64 },
                                },
                              ];
                              return false;
                            } else {
                              if (func51(data7) < 64) {
                                validate13.errors = [
                                  {
                                    instancePath: instancePath + '/client_nonce',
                                    schemaPath: '#/definitions/Nonce/minLength',
                                    keyword: 'minLength',
                                    params: { limit: 64 },
                                  },
                                ];
                                return false;
                              } else {
                                if (!pattern0.test(data7)) {
                                  validate13.errors = [
                                    {
                                      instancePath: instancePath + '/client_nonce',
                                      schemaPath: '#/definitions/Nonce/pattern',
                                      keyword: 'pattern',
                                      params: { pattern: '^[a-f0-9]{64}$' },
                                    },
                                  ];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate13.errors = [
                              {
                                instancePath: instancePath + '/client_nonce',
                                schemaPath: '#/definitions/Nonce/type',
                                keyword: 'type',
                                params: { type: 'string' },
                              },
                            ];
                            return false;
                          }
                        }
                        var valid0 = _errs17 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.client_proof !== void 0 && func0.call(data, 'client_proof')) {
                          let data8 = data.client_proof;
                          const _errs20 = errors;
                          const _errs21 = errors;
                          if (errors === _errs21) {
                            if (typeof data8 === 'string') {
                              if (func51(data8) > 64) {
                                validate13.errors = [
                                  {
                                    instancePath: instancePath + '/client_proof',
                                    schemaPath: '#/definitions/Signature/maxLength',
                                    keyword: 'maxLength',
                                    params: { limit: 64 },
                                  },
                                ];
                                return false;
                              } else {
                                if (func51(data8) < 64) {
                                  validate13.errors = [
                                    {
                                      instancePath: instancePath + '/client_proof',
                                      schemaPath: '#/definitions/Signature/minLength',
                                      keyword: 'minLength',
                                      params: { limit: 64 },
                                    },
                                  ];
                                  return false;
                                } else {
                                  if (!pattern0.test(data8)) {
                                    validate13.errors = [
                                      {
                                        instancePath: instancePath + '/client_proof',
                                        schemaPath: '#/definitions/Signature/pattern',
                                        keyword: 'pattern',
                                        params: { pattern: '^[a-f0-9]{64}$' },
                                      },
                                    ];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate13.errors = [
                                {
                                  instancePath: instancePath + '/client_proof',
                                  schemaPath: '#/definitions/Signature/type',
                                  keyword: 'type',
                                  params: { type: 'string' },
                                },
                              ];
                              return false;
                            }
                          }
                          var valid0 = _errs20 === errors;
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
      }
    } else {
      validate13.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate13.errors = vErrors;
  return errors === 0;
}
var schema18 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'capabilities', 'server_signature'],
  properties: {
    type: { type: 'string', enum: ['welcome'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    capabilities: { $ref: '#/definitions/Capabilities' },
    server_signature: { $ref: '#/definitions/Signature' },
  },
};
var pattern6 = new RegExp('^[a-f0-9]{32}$', 'u');
function validate15(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.capabilities === void 0 || !func0.call(data, 'capabilities')) && (missing0 = 'capabilities')) ||
        ((data.server_signature === void 0 || !func0.call(data, 'server_signature')) && (missing0 = 'server_signature'))
      ) {
        validate15.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
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
            key0 === 'server_signature'
          )) {
            validate15.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
                },
              ];
              return false;
            }
            if (!(data0 === 'welcome')) {
              validate15.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema18.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate15.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate15.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema18.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate15.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate15.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate15.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
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
                if (data.capabilities !== void 0 && func0.call(data, 'capabilities')) {
                  let data3 = data.capabilities;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (Array.isArray(data3)) {
                      if (data3.length > 0) {
                        validate15.errors = [
                          {
                            instancePath: instancePath + '/capabilities',
                            schemaPath: '#/definitions/Capabilities/maxItems',
                            keyword: 'maxItems',
                            params: { limit: 0 },
                          },
                        ];
                        return false;
                      } else {
                        var valid3 = true;
                        const len0 = data3.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs12 = errors;
                          if (typeof data3[i0] !== 'string') {
                            validate15.errors = [
                              {
                                instancePath: instancePath + '/capabilities/' + i0,
                                schemaPath: '#/definitions/Capabilities/items/type',
                                keyword: 'type',
                                params: { type: 'string' },
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
                                validate15.errors = [
                                  {
                                    instancePath: instancePath + '/capabilities',
                                    schemaPath: '#/definitions/Capabilities/uniqueItems',
                                    keyword: 'uniqueItems',
                                    params: { i: i1, j: j0 },
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
                      validate15.errors = [
                        {
                          instancePath: instancePath + '/capabilities',
                          schemaPath: '#/definitions/Capabilities/type',
                          keyword: 'type',
                          params: { type: 'array' },
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
                  if (data.server_signature !== void 0 && func0.call(data, 'server_signature')) {
                    let data5 = data.server_signature;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (typeof data5 === 'string') {
                        if (func51(data5) > 64) {
                          validate15.errors = [
                            {
                              instancePath: instancePath + '/server_signature',
                              schemaPath: '#/definitions/Signature/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data5) < 64) {
                            validate15.errors = [
                              {
                                instancePath: instancePath + '/server_signature',
                                schemaPath: '#/definitions/Signature/minLength',
                                keyword: 'minLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data5)) {
                              validate15.errors = [
                                {
                                  instancePath: instancePath + '/server_signature',
                                  schemaPath: '#/definitions/Signature/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[a-f0-9]{64}$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate15.errors = [
                          {
                            instancePath: instancePath + '/server_signature',
                            schemaPath: '#/definitions/Signature/type',
                            keyword: 'type',
                            params: { type: 'string' },
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
    } else {
      validate15.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate15.errors = vErrors;
  return errors === 0;
}
var schema22 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'sequence', 'mac'],
  properties: {
    type: { type: 'string', enum: ['ping'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    sequence: { type: 'integer', minimum: 1, maximum: 2147483647 },
    mac: { $ref: '#/definitions/Signature' },
  },
};
function validate17(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.sequence === void 0 || !func0.call(data, 'sequence')) && (missing0 = 'sequence')) ||
        ((data.mac === void 0 || !func0.call(data, 'mac')) && (missing0 = 'mac'))
      ) {
        validate17.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'sequence' ||
            key0 === 'mac'
          )) {
            validate17.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
                },
              ];
              return false;
            }
            if (!(data0 === 'ping')) {
              validate17.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema22.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate17.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate17.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema22.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate17.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate17.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate17.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
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
                  if (!(typeof data3 == 'number' && !(data3 % 1) && !isNaN(data3) && isFinite(data3))) {
                    validate17.errors = [
                      {
                        instancePath: instancePath + '/sequence',
                        schemaPath: '#/properties/sequence/type',
                        keyword: 'type',
                        params: { type: 'integer' },
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
                if (valid0) {
                  if (data.mac !== void 0 && func0.call(data, 'mac')) {
                    let data4 = data.mac;
                    const _errs11 = errors;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 64) {
                          validate17.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 64) {
                            validate17.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/minLength',
                                keyword: 'minLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data4)) {
                              validate17.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[a-f0-9]{64}$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate17.errors = [
                          {
                            instancePath: instancePath + '/mac',
                            schemaPath: '#/definitions/Signature/type',
                            keyword: 'type',
                            params: { type: 'string' },
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs11 === errors;
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
      validate17.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate17.errors = vErrors;
  return errors === 0;
}
var schema25 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'sequence', 'mac'],
  properties: {
    type: { type: 'string', enum: ['pong'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    sequence: { type: 'integer', minimum: 1, maximum: 2147483647 },
    mac: { $ref: '#/definitions/Signature' },
  },
};
function validate19(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.sequence === void 0 || !func0.call(data, 'sequence')) && (missing0 = 'sequence')) ||
        ((data.mac === void 0 || !func0.call(data, 'mac')) && (missing0 = 'mac'))
      ) {
        validate19.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'sequence' ||
            key0 === 'mac'
          )) {
            validate19.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
                },
              ];
              return false;
            }
            if (!(data0 === 'pong')) {
              validate19.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema25.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate19.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate19.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema25.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate19.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate19.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate19.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
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
                  if (!(typeof data3 == 'number' && !(data3 % 1) && !isNaN(data3) && isFinite(data3))) {
                    validate19.errors = [
                      {
                        instancePath: instancePath + '/sequence',
                        schemaPath: '#/properties/sequence/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs9) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate19.errors = [
                          {
                            instancePath: instancePath + '/sequence',
                            schemaPath: '#/properties/sequence/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate19.errors = [
                            {
                              instancePath: instancePath + '/sequence',
                              schemaPath: '#/properties/sequence/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
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
                if (valid0) {
                  if (data.mac !== void 0 && func0.call(data, 'mac')) {
                    let data4 = data.mac;
                    const _errs11 = errors;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 64) {
                          validate19.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 64) {
                            validate19.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/minLength',
                                keyword: 'minLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data4)) {
                              validate19.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[a-f0-9]{64}$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate19.errors = [
                          {
                            instancePath: instancePath + '/mac',
                            schemaPath: '#/definitions/Signature/type',
                            keyword: 'type',
                            params: { type: 'string' },
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs11 === errors;
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
      validate19.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate19.errors = vErrors;
  return errors === 0;
}
var schema28 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'code'],
  properties: {
    type: { type: 'string', enum: ['error'] },
    protocol_version: { type: 'integer', enum: [2] },
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
    mac: { $ref: '#/definitions/Signature' },
  },
};
function validate21(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.code === void 0 || !func0.call(data, 'code')) && (missing0 = 'code'))
      ) {
        validate21.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'code' ||
            key0 === 'mac'
          )) {
            validate21.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate21.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'error')) {
              validate21.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema28.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate21.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate21.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema28.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate21.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate21.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate21.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate21.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                    validate21.errors = [
                      {
                        instancePath: instancePath + '/code',
                        schemaPath: '#/properties/code/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                    validate21.errors = [
                      {
                        instancePath: instancePath + '/code',
                        schemaPath: '#/properties/code/enum',
                        keyword: 'enum',
                        params: { allowedValues: schema28.properties.code.enum },
                      },
                    ];
                    return false;
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.mac !== void 0 && func0.call(data, 'mac')) {
                    let data4 = data.mac;
                    const _errs11 = errors;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 64) {
                          validate21.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 64) {
                            validate21.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/minLength',
                                keyword: 'minLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data4)) {
                              validate21.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[a-f0-9]{64}$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate21.errors = [
                          {
                            instancePath: instancePath + '/mac',
                            schemaPath: '#/definitions/Signature/type',
                            keyword: 'type',
                            params: { type: 'string' },
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs11 === errors;
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
      validate21.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate21.errors = vErrors;
  return errors === 0;
}
var schema31 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'request_id', 'operation', 'mac'],
  properties: {
    type: { type: 'string', enum: ['request'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    request_id: { $ref: '#/definitions/RequestId' },
    operation: { $ref: '#/definitions/Operation' },
    mac: { $ref: '#/definitions/Signature' },
  },
};
var schema35 = {
  type: 'object',
  additionalProperties: false,
  required: ['name'],
  properties: { name: { type: 'string', enum: ['list_accounts'] } },
};
var schema36 = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'account'],
  properties: { name: { type: 'string', enum: ['list_mailboxes'] }, account: { $ref: '#/definitions/Handle' } },
};
var pattern15 = new RegExp('^[A-Za-z0-9_-]{22}$', 'u');
function validate25(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.account === void 0 || !func0.call(data, 'account')) && (missing0 = 'account'))
      ) {
        validate25.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'name' || key0 === 'account')) {
            validate25.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.name !== void 0 && func0.call(data, 'name')) {
            let data0 = data.name;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate25.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'list_mailboxes')) {
              validate25.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema36.properties.name.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.account !== void 0 && func0.call(data, 'account')) {
              let data1 = data.account;
              const _errs4 = errors;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 22) {
                    validate25.errors = [
                      {
                        instancePath: instancePath + '/account',
                        schemaPath: '#/definitions/Handle/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 22) {
                      validate25.errors = [
                        {
                          instancePath: instancePath + '/account',
                          schemaPath: '#/definitions/Handle/minLength',
                          keyword: 'minLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (!pattern15.test(data1)) {
                        validate25.errors = [
                          {
                            instancePath: instancePath + '/account',
                            schemaPath: '#/definitions/Handle/pattern',
                            keyword: 'pattern',
                            params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                          },
                        ];
                        return false;
                      }
                    }
                  }
                } else {
                  validate25.errors = [
                    {
                      instancePath: instancePath + '/account',
                      schemaPath: '#/definitions/Handle/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate25.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate25.errors = vErrors;
  return errors === 0;
}
var schema38 = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'mailbox'],
  properties: { name: { type: 'string', enum: ['list_messages'] }, mailbox: { $ref: '#/definitions/Handle' } },
};
function validate27(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.mailbox === void 0 || !func0.call(data, 'mailbox')) && (missing0 = 'mailbox'))
      ) {
        validate27.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'name' || key0 === 'mailbox')) {
            validate27.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.name !== void 0 && func0.call(data, 'name')) {
            let data0 = data.name;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate27.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'list_messages')) {
              validate27.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema38.properties.name.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.mailbox !== void 0 && func0.call(data, 'mailbox')) {
              let data1 = data.mailbox;
              const _errs4 = errors;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 22) {
                    validate27.errors = [
                      {
                        instancePath: instancePath + '/mailbox',
                        schemaPath: '#/definitions/Handle/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 22) {
                      validate27.errors = [
                        {
                          instancePath: instancePath + '/mailbox',
                          schemaPath: '#/definitions/Handle/minLength',
                          keyword: 'minLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (!pattern15.test(data1)) {
                        validate27.errors = [
                          {
                            instancePath: instancePath + '/mailbox',
                            schemaPath: '#/definitions/Handle/pattern',
                            keyword: 'pattern',
                            params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                          },
                        ];
                        return false;
                      }
                    }
                  }
                } else {
                  validate27.errors = [
                    {
                      instancePath: instancePath + '/mailbox',
                      schemaPath: '#/definitions/Handle/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate27.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate27.errors = vErrors;
  return errors === 0;
}
var schema40 = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'cursor'],
  properties: { name: { type: 'string', enum: ['continue_list'] }, cursor: { $ref: '#/definitions/Handle' } },
};
function validate29(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.cursor === void 0 || !func0.call(data, 'cursor')) && (missing0 = 'cursor'))
      ) {
        validate29.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'name' || key0 === 'cursor')) {
            validate29.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.name !== void 0 && func0.call(data, 'name')) {
            let data0 = data.name;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate29.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'continue_list')) {
              validate29.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema40.properties.name.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.cursor !== void 0 && func0.call(data, 'cursor')) {
              let data1 = data.cursor;
              const _errs4 = errors;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 22) {
                    validate29.errors = [
                      {
                        instancePath: instancePath + '/cursor',
                        schemaPath: '#/definitions/Handle/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 22) {
                      validate29.errors = [
                        {
                          instancePath: instancePath + '/cursor',
                          schemaPath: '#/definitions/Handle/minLength',
                          keyword: 'minLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (!pattern15.test(data1)) {
                        validate29.errors = [
                          {
                            instancePath: instancePath + '/cursor',
                            schemaPath: '#/definitions/Handle/pattern',
                            keyword: 'pattern',
                            params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                          },
                        ];
                        return false;
                      }
                    }
                  }
                } else {
                  validate29.errors = [
                    {
                      instancePath: instancePath + '/cursor',
                      schemaPath: '#/definitions/Handle/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate29.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate29.errors = vErrors;
  return errors === 0;
}
var schema42 = {
  type: 'object',
  additionalProperties: false,
  required: ['name', 'cursor'],
  properties: { name: { type: 'string', enum: ['close_list'] }, cursor: { $ref: '#/definitions/Handle' } },
};
function validate31(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.cursor === void 0 || !func0.call(data, 'cursor')) && (missing0 = 'cursor'))
      ) {
        validate31.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'name' || key0 === 'cursor')) {
            validate31.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.name !== void 0 && func0.call(data, 'name')) {
            let data0 = data.name;
            const _errs2 = errors;
            if (typeof data0 !== 'string') {
              validate31.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'close_list')) {
              validate31.errors = [
                {
                  instancePath: instancePath + '/name',
                  schemaPath: '#/properties/name/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema42.properties.name.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.cursor !== void 0 && func0.call(data, 'cursor')) {
              let data1 = data.cursor;
              const _errs4 = errors;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 22) {
                    validate31.errors = [
                      {
                        instancePath: instancePath + '/cursor',
                        schemaPath: '#/definitions/Handle/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 22) {
                      validate31.errors = [
                        {
                          instancePath: instancePath + '/cursor',
                          schemaPath: '#/definitions/Handle/minLength',
                          keyword: 'minLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (!pattern15.test(data1)) {
                        validate31.errors = [
                          {
                            instancePath: instancePath + '/cursor',
                            schemaPath: '#/definitions/Handle/pattern',
                            keyword: 'pattern',
                            params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                          },
                        ];
                        return false;
                      }
                    }
                  }
                } else {
                  validate31.errors = [
                    {
                      instancePath: instancePath + '/cursor',
                      schemaPath: '#/definitions/Handle/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate31.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate31.errors = vErrors;
  return errors === 0;
}
function validate24(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  const _errs0 = errors;
  let valid0 = false;
  let passing0 = null;
  const _errs1 = errors;
  const _errs2 = errors;
  if (errors === _errs2) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) {
        const err0 = {
          instancePath,
          schemaPath: '#/definitions/ListAccounts/required',
          keyword: 'required',
          params: { missingProperty: missing0 },
        };
        if (vErrors === null) {
          vErrors = [err0];
        } else {
          vErrors.push(err0);
        }
        errors++;
      } else {
        const _errs4 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'name')) {
            const err1 = {
              instancePath,
              schemaPath: '#/definitions/ListAccounts/additionalProperties',
              keyword: 'additionalProperties',
              params: { additionalProperty: key0 },
            };
            if (vErrors === null) {
              vErrors = [err1];
            } else {
              vErrors.push(err1);
            }
            errors++;
            break;
          }
        }
        if (_errs4 === errors) {
          if (data.name !== void 0 && func0.call(data, 'name')) {
            let data0 = data.name;
            if (typeof data0 !== 'string') {
              const err2 = {
                instancePath: instancePath + '/name',
                schemaPath: '#/definitions/ListAccounts/properties/name/type',
                keyword: 'type',
                params: { type: 'string' },
              };
              if (vErrors === null) {
                vErrors = [err2];
              } else {
                vErrors.push(err2);
              }
              errors++;
            }
            if (!(data0 === 'list_accounts')) {
              const err3 = {
                instancePath: instancePath + '/name',
                schemaPath: '#/definitions/ListAccounts/properties/name/enum',
                keyword: 'enum',
                params: { allowedValues: schema35.properties.name.enum },
              };
              if (vErrors === null) {
                vErrors = [err3];
              } else {
                vErrors.push(err3);
              }
              errors++;
            }
          }
        }
      }
    } else {
      const err4 = {
        instancePath,
        schemaPath: '#/definitions/ListAccounts/type',
        keyword: 'type',
        params: { type: 'object' },
      };
      if (vErrors === null) {
        vErrors = [err4];
      } else {
        vErrors.push(err4);
      }
      errors++;
    }
  }
  var _valid0 = _errs1 === errors;
  if (_valid0) {
    valid0 = true;
    passing0 = 0;
  }
  const _errs7 = errors;
  if (!validate25(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
    errors = vErrors.length;
  }
  var _valid0 = _errs7 === errors;
  if (_valid0 && valid0) {
    valid0 = false;
    passing0 = [passing0, 1];
  } else {
    if (_valid0) {
      valid0 = true;
      passing0 = 1;
    }
    const _errs8 = errors;
    if (!validate27(data, { instancePath, parentData, parentDataProperty, rootData })) {
      vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
      errors = vErrors.length;
    }
    var _valid0 = _errs8 === errors;
    if (_valid0 && valid0) {
      valid0 = false;
      passing0 = [passing0, 2];
    } else {
      if (_valid0) {
        valid0 = true;
        passing0 = 2;
      }
      const _errs9 = errors;
      if (!validate29(data, { instancePath, parentData, parentDataProperty, rootData })) {
        vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
        errors = vErrors.length;
      }
      var _valid0 = _errs9 === errors;
      if (_valid0 && valid0) {
        valid0 = false;
        passing0 = [passing0, 3];
      } else {
        if (_valid0) {
          valid0 = true;
          passing0 = 3;
        }
        const _errs10 = errors;
        if (!validate31(data, { instancePath, parentData, parentDataProperty, rootData })) {
          vErrors = vErrors === null ? validate31.errors : vErrors.concat(validate31.errors);
          errors = vErrors.length;
        }
        var _valid0 = _errs10 === errors;
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
    const err5 = { instancePath, schemaPath: '#/oneOf', keyword: 'oneOf', params: { passingSchemas: passing0 } };
    if (vErrors === null) {
      vErrors = [err5];
    } else {
      vErrors.push(err5);
    }
    errors++;
    validate24.errors = vErrors;
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
  validate24.errors = vErrors;
  return errors === 0;
}
function validate23(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.request_id === void 0 || !func0.call(data, 'request_id')) && (missing0 = 'request_id')) ||
        ((data.operation === void 0 || !func0.call(data, 'operation')) && (missing0 = 'operation')) ||
        ((data.mac === void 0 || !func0.call(data, 'mac')) && (missing0 = 'mac'))
      ) {
        validate23.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'request_id' ||
            key0 === 'operation' ||
            key0 === 'mac'
          )) {
            validate23.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate23.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'request')) {
              validate23.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema31.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate23.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate23.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema31.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate23.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate23.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate23.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate23.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.request_id !== void 0 && func0.call(data, 'request_id')) {
                  let data3 = data.request_id;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (!(typeof data3 == 'number' && !(data3 % 1) && !isNaN(data3) && isFinite(data3))) {
                    validate23.errors = [
                      {
                        instancePath: instancePath + '/request_id',
                        schemaPath: '#/definitions/RequestId/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs10) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate23.errors = [
                          {
                            instancePath: instancePath + '/request_id',
                            schemaPath: '#/definitions/RequestId/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate23.errors = [
                            {
                              instancePath: instancePath + '/request_id',
                              schemaPath: '#/definitions/RequestId/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
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
                if (valid0) {
                  if (data.operation !== void 0 && func0.call(data, 'operation')) {
                    const _errs12 = errors;
                    if (
                      !validate24(data.operation, {
                        instancePath: instancePath + '/operation',
                        parentData: data,
                        parentDataProperty: 'operation',
                        rootData,
                      })
                    ) {
                      vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.mac !== void 0 && func0.call(data, 'mac')) {
                      let data5 = data.mac;
                      const _errs13 = errors;
                      const _errs14 = errors;
                      if (errors === _errs14) {
                        if (typeof data5 === 'string') {
                          if (func51(data5) > 64) {
                            validate23.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/maxLength',
                                keyword: 'maxLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (func51(data5) < 64) {
                              validate23.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/minLength',
                                  keyword: 'minLength',
                                  params: { limit: 64 },
                                },
                              ];
                              return false;
                            } else {
                              if (!pattern0.test(data5)) {
                                validate23.errors = [
                                  {
                                    instancePath: instancePath + '/mac',
                                    schemaPath: '#/definitions/Signature/pattern',
                                    keyword: 'pattern',
                                    params: { pattern: '^[a-f0-9]{64}$' },
                                  },
                                ];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate23.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/type',
                              keyword: 'type',
                              params: { type: 'string' },
                            },
                          ];
                          return false;
                        }
                      }
                      var valid0 = _errs13 === errors;
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
      validate23.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate23.errors = vErrors;
  return errors === 0;
}
var schema45 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'request_id', 'mac'],
  properties: {
    type: { type: 'string', enum: ['cancel'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    request_id: { $ref: '#/definitions/RequestId' },
    mac: { $ref: '#/definitions/Signature' },
  },
};
function validate35(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.request_id === void 0 || !func0.call(data, 'request_id')) && (missing0 = 'request_id')) ||
        ((data.mac === void 0 || !func0.call(data, 'mac')) && (missing0 = 'mac'))
      ) {
        validate35.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'request_id' ||
            key0 === 'mac'
          )) {
            validate35.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate35.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'cancel')) {
              validate35.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema45.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate35.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate35.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema45.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate35.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate35.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate35.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate35.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.request_id !== void 0 && func0.call(data, 'request_id')) {
                  let data3 = data.request_id;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (!(typeof data3 == 'number' && !(data3 % 1) && !isNaN(data3) && isFinite(data3))) {
                    validate35.errors = [
                      {
                        instancePath: instancePath + '/request_id',
                        schemaPath: '#/definitions/RequestId/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs10) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate35.errors = [
                          {
                            instancePath: instancePath + '/request_id',
                            schemaPath: '#/definitions/RequestId/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate35.errors = [
                            {
                              instancePath: instancePath + '/request_id',
                              schemaPath: '#/definitions/RequestId/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
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
                if (valid0) {
                  if (data.mac !== void 0 && func0.call(data, 'mac')) {
                    let data4 = data.mac;
                    const _errs12 = errors;
                    const _errs13 = errors;
                    if (errors === _errs13) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 64) {
                          validate35.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 64 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 64) {
                            validate35.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/minLength',
                                keyword: 'minLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern0.test(data4)) {
                              validate35.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[a-f0-9]{64}$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate35.errors = [
                          {
                            instancePath: instancePath + '/mac',
                            schemaPath: '#/definitions/Signature/type',
                            keyword: 'type',
                            params: { type: 'string' },
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
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
      validate35.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate35.errors = vErrors;
  return errors === 0;
}
var schema49 = {
  type: 'object',
  additionalProperties: false,
  required: ['type', 'protocol_version', 'generation', 'request_id', 'result', 'mac'],
  properties: {
    type: { type: 'string', enum: ['reply'] },
    protocol_version: { type: 'integer', enum: [2] },
    generation: { $ref: '#/definitions/Generation' },
    request_id: { $ref: '#/definitions/RequestId' },
    result: { $ref: '#/definitions/Outcome' },
    mac: { $ref: '#/definitions/Signature' },
  },
};
var schema68 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind'],
  properties: { kind: { type: 'string', enum: ['closed'] } },
};
var schema53 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind', 'accounts'],
  properties: {
    kind: { type: 'string', enum: ['accounts'] },
    accounts: { type: 'array', items: { $ref: '#/definitions/Account' } },
  },
};
function validate41(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.id === void 0 || !func0.call(data, 'id')) && (missing0 = 'id')) ||
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.email === void 0 || !func0.call(data, 'email')) && (missing0 = 'email'))
      ) {
        validate41.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'email')) {
            validate41.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0 && func0.call(data, 'id')) {
            let data0 = data.id;
            const _errs2 = errors;
            const _errs3 = errors;
            if (errors === _errs3) {
              if (typeof data0 === 'string') {
                if (func51(data0) > 22) {
                  validate41.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 22 },
                    },
                  ];
                  return false;
                } else {
                  if (func51(data0) < 22) {
                    validate41.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern15.test(data0)) {
                      validate41.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate41.errors = [
                  {
                    instancePath: instancePath + '/id',
                    schemaPath: '#/definitions/Handle/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  },
                ];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0 && func0.call(data, 'name')) {
              let data1 = data.name;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 128) {
                    validate41.errors = [
                      {
                        instancePath: instancePath + '/name',
                        schemaPath: '#/properties/name/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 128 },
                      },
                    ];
                    return false;
                  }
                } else {
                  validate41.errors = [
                    {
                      instancePath: instancePath + '/name',
                      schemaPath: '#/properties/name/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.email !== void 0 && func0.call(data, 'email')) {
                let data2 = data.email;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 254) {
                      validate41.errors = [
                        {
                          instancePath: instancePath + '/email',
                          schemaPath: '#/properties/email/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 254 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 1) {
                        validate41.errors = [
                          {
                            instancePath: instancePath + '/email',
                            schemaPath: '#/properties/email/minLength',
                            keyword: 'minLength',
                            params: { limit: 1 },
                          },
                        ];
                        return false;
                      }
                    }
                  } else {
                    validate41.errors = [
                      {
                        instancePath: instancePath + '/email',
                        schemaPath: '#/properties/email/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
      validate41.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate41.errors = vErrors;
  return errors === 0;
}
function validate40(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.id === void 0 || !func0.call(data, 'id')) && (missing0 = 'id')) ||
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name')) ||
        ((data.identities === void 0 || !func0.call(data, 'identities')) && (missing0 = 'identities'))
      ) {
        validate40.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'identities')) {
            validate40.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0 && func0.call(data, 'id')) {
            let data0 = data.id;
            const _errs2 = errors;
            const _errs3 = errors;
            if (errors === _errs3) {
              if (typeof data0 === 'string') {
                if (func51(data0) > 22) {
                  validate40.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 22 },
                    },
                  ];
                  return false;
                } else {
                  if (func51(data0) < 22) {
                    validate40.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern15.test(data0)) {
                      validate40.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate40.errors = [
                  {
                    instancePath: instancePath + '/id',
                    schemaPath: '#/definitions/Handle/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  },
                ];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0 && func0.call(data, 'name')) {
              let data1 = data.name;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 128) {
                    validate40.errors = [
                      {
                        instancePath: instancePath + '/name',
                        schemaPath: '#/properties/name/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 128 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 1) {
                      validate40.errors = [
                        {
                          instancePath: instancePath + '/name',
                          schemaPath: '#/properties/name/minLength',
                          keyword: 'minLength',
                          params: { limit: 1 },
                        },
                      ];
                      return false;
                    }
                  }
                } else {
                  validate40.errors = [
                    {
                      instancePath: instancePath + '/name',
                      schemaPath: '#/properties/name/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.identities !== void 0 && func0.call(data, 'identities')) {
                let data2 = data.identities;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (Array.isArray(data2)) {
                    var valid2 = true;
                    const len0 = data2.length;
                    for (let i0 = 0; i0 < len0; i0++) {
                      const _errs9 = errors;
                      if (
                        !validate41(data2[i0], {
                          instancePath: instancePath + '/identities/' + i0,
                          parentData: data2,
                          parentDataProperty: i0,
                          rootData,
                        })
                      ) {
                        vErrors = vErrors === null ? validate41.errors : vErrors.concat(validate41.errors);
                        errors = vErrors.length;
                      }
                      var valid2 = _errs9 === errors;
                      if (!valid2) {
                        break;
                      }
                    }
                  } else {
                    validate40.errors = [
                      {
                        instancePath: instancePath + '/identities',
                        schemaPath: '#/properties/identities/type',
                        keyword: 'type',
                        params: { type: 'array' },
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
      validate40.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate40.errors = vErrors;
  return errors === 0;
}
function validate39(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) ||
        ((data.accounts === void 0 || !func0.call(data, 'accounts')) && (missing0 = 'accounts'))
      ) {
        validate39.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'kind' || key0 === 'accounts')) {
            validate39.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate39.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'accounts')) {
              validate39.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema53.properties.kind.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.accounts !== void 0 && func0.call(data, 'accounts')) {
              let data1 = data.accounts;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (
                      !validate40(data1[i0], {
                        instancePath: instancePath + '/accounts/' + i0,
                        parentData: data1,
                        parentDataProperty: i0,
                        rootData,
                      })
                    ) {
                      vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                      errors = vErrors.length;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate39.errors = [
                    {
                      instancePath: instancePath + '/accounts',
                      schemaPath: '#/properties/accounts/type',
                      keyword: 'type',
                      params: { type: 'array' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate39.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate39.errors = vErrors;
  return errors === 0;
}
var schema58 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind', 'mailboxes'],
  properties: {
    kind: { type: 'string', enum: ['mailboxes'] },
    mailboxes: { type: 'array', items: { $ref: '#/definitions/Mailbox' } },
    cursor: { $ref: '#/definitions/Handle' },
  },
};
var schema62 = { type: 'string', enum: ['inbox', 'drafts', 'sent', 'trash', 'archive', 'junk', 'templates', 'outbox'] };
function validate46(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.id === void 0 || !func0.call(data, 'id')) && (missing0 = 'id')) ||
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name'))
      ) {
        validate46.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'parent' || key0 === 'role')) {
            validate46.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0 && func0.call(data, 'id')) {
            let data0 = data.id;
            const _errs2 = errors;
            const _errs3 = errors;
            if (errors === _errs3) {
              if (typeof data0 === 'string') {
                if (func51(data0) > 22) {
                  validate46.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 22 },
                    },
                  ];
                  return false;
                } else {
                  if (func51(data0) < 22) {
                    validate46.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern15.test(data0)) {
                      validate46.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate46.errors = [
                  {
                    instancePath: instancePath + '/id',
                    schemaPath: '#/definitions/Handle/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  },
                ];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0 && func0.call(data, 'name')) {
              let data1 = data.name;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 255) {
                    validate46.errors = [
                      {
                        instancePath: instancePath + '/name',
                        schemaPath: '#/properties/name/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 255 },
                      },
                    ];
                    return false;
                  } else {
                    if (func51(data1) < 1) {
                      validate46.errors = [
                        {
                          instancePath: instancePath + '/name',
                          schemaPath: '#/properties/name/minLength',
                          keyword: 'minLength',
                          params: { limit: 1 },
                        },
                      ];
                      return false;
                    }
                  }
                } else {
                  validate46.errors = [
                    {
                      instancePath: instancePath + '/name',
                      schemaPath: '#/properties/name/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.parent !== void 0 && func0.call(data, 'parent')) {
                let data2 = data.parent;
                const _errs7 = errors;
                const _errs8 = errors;
                if (errors === _errs8) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 22) {
                      validate46.errors = [
                        {
                          instancePath: instancePath + '/parent',
                          schemaPath: '#/definitions/Handle/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 22) {
                        validate46.errors = [
                          {
                            instancePath: instancePath + '/parent',
                            schemaPath: '#/definitions/Handle/minLength',
                            keyword: 'minLength',
                            params: { limit: 22 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern15.test(data2)) {
                          validate46.errors = [
                            {
                              instancePath: instancePath + '/parent',
                              schemaPath: '#/definitions/Handle/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate46.errors = [
                      {
                        instancePath: instancePath + '/parent',
                        schemaPath: '#/definitions/Handle/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.role !== void 0 && func0.call(data, 'role')) {
                  let data3 = data.role;
                  const _errs10 = errors;
                  if (typeof data3 !== 'string') {
                    validate46.errors = [
                      {
                        instancePath: instancePath + '/role',
                        schemaPath: '#/definitions/MailboxRole/type',
                        keyword: 'type',
                        params: { type: 'string' },
                      },
                    ];
                    return false;
                  }
                  if (!(
                    data3 === 'inbox' ||
                    data3 === 'drafts' ||
                    data3 === 'sent' ||
                    data3 === 'trash' ||
                    data3 === 'archive' ||
                    data3 === 'junk' ||
                    data3 === 'templates' ||
                    data3 === 'outbox'
                  )) {
                    validate46.errors = [
                      {
                        instancePath: instancePath + '/role',
                        schemaPath: '#/definitions/MailboxRole/enum',
                        keyword: 'enum',
                        params: { allowedValues: schema62.enum },
                      },
                    ];
                    return false;
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
    } else {
      validate46.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate46.errors = vErrors;
  return errors === 0;
}
function validate45(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) ||
        ((data.mailboxes === void 0 || !func0.call(data, 'mailboxes')) && (missing0 = 'mailboxes'))
      ) {
        validate45.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'kind' || key0 === 'mailboxes' || key0 === 'cursor')) {
            validate45.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate45.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'mailboxes')) {
              validate45.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema58.properties.kind.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.mailboxes !== void 0 && func0.call(data, 'mailboxes')) {
              let data1 = data.mailboxes;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (
                      !validate46(data1[i0], {
                        instancePath: instancePath + '/mailboxes/' + i0,
                        parentData: data1,
                        parentDataProperty: i0,
                        rootData,
                      })
                    ) {
                      vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
                      errors = vErrors.length;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate45.errors = [
                    {
                      instancePath: instancePath + '/mailboxes',
                      schemaPath: '#/properties/mailboxes/type',
                      keyword: 'type',
                      params: { type: 'array' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.cursor !== void 0 && func0.call(data, 'cursor')) {
                let data3 = data.cursor;
                const _errs7 = errors;
                const _errs8 = errors;
                if (errors === _errs8) {
                  if (typeof data3 === 'string') {
                    if (func51(data3) > 22) {
                      validate45.errors = [
                        {
                          instancePath: instancePath + '/cursor',
                          schemaPath: '#/definitions/Handle/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data3) < 22) {
                        validate45.errors = [
                          {
                            instancePath: instancePath + '/cursor',
                            schemaPath: '#/definitions/Handle/minLength',
                            keyword: 'minLength',
                            params: { limit: 22 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern15.test(data3)) {
                          validate45.errors = [
                            {
                              instancePath: instancePath + '/cursor',
                              schemaPath: '#/definitions/Handle/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate45.errors = [
                      {
                        instancePath: instancePath + '/cursor',
                        schemaPath: '#/definitions/Handle/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
      validate45.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate45.errors = vErrors;
  return errors === 0;
}
var schema64 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind', 'messages'],
  properties: {
    kind: { type: 'string', enum: ['messages'] },
    messages: { type: 'array', items: { $ref: '#/definitions/MessageSummary' } },
    cursor: { $ref: '#/definitions/Handle' },
  },
};
var pattern29 = new RegExp('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$', 'u');
function validate50(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.id === void 0 || !func0.call(data, 'id')) && (missing0 = 'id')) ||
        ((data.subject === void 0 || !func0.call(data, 'subject')) && (missing0 = 'subject')) ||
        ((data.author === void 0 || !func0.call(data, 'author')) && (missing0 = 'author')) ||
        ((data.recipients === void 0 || !func0.call(data, 'recipients')) && (missing0 = 'recipients')) ||
        ((data.date === void 0 || !func0.call(data, 'date')) && (missing0 = 'date')) ||
        ((data.read === void 0 || !func0.call(data, 'read')) && (missing0 = 'read')) ||
        ((data.flagged === void 0 || !func0.call(data, 'flagged')) && (missing0 = 'flagged'))
      ) {
        validate50.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'id' ||
            key0 === 'subject' ||
            key0 === 'author' ||
            key0 === 'recipients' ||
            key0 === 'date' ||
            key0 === 'read' ||
            key0 === 'flagged'
          )) {
            validate50.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
              },
            ];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0 && func0.call(data, 'id')) {
            let data0 = data.id;
            const _errs2 = errors;
            const _errs3 = errors;
            if (errors === _errs3) {
              if (typeof data0 === 'string') {
                if (func51(data0) > 22) {
                  validate50.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 22 },
                    },
                  ];
                  return false;
                } else {
                  if (func51(data0) < 22) {
                    validate50.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 22 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern15.test(data0)) {
                      validate50.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate50.errors = [
                  {
                    instancePath: instancePath + '/id',
                    schemaPath: '#/definitions/Handle/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  },
                ];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.subject !== void 0 && func0.call(data, 'subject')) {
              let data1 = data.subject;
              const _errs5 = errors;
              if (errors === _errs5) {
                if (typeof data1 === 'string') {
                  if (func51(data1) > 300) {
                    validate50.errors = [
                      {
                        instancePath: instancePath + '/subject',
                        schemaPath: '#/properties/subject/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 300 },
                      },
                    ];
                    return false;
                  }
                } else {
                  validate50.errors = [
                    {
                      instancePath: instancePath + '/subject',
                      schemaPath: '#/properties/subject/type',
                      keyword: 'type',
                      params: { type: 'string' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.author !== void 0 && func0.call(data, 'author')) {
                let data2 = data.author;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 300) {
                      validate50.errors = [
                        {
                          instancePath: instancePath + '/author',
                          schemaPath: '#/properties/author/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 300 },
                        },
                      ];
                      return false;
                    }
                  } else {
                    validate50.errors = [
                      {
                        instancePath: instancePath + '/author',
                        schemaPath: '#/properties/author/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.recipients !== void 0 && func0.call(data, 'recipients')) {
                  let data3 = data.recipients;
                  const _errs9 = errors;
                  if (errors === _errs9) {
                    if (typeof data3 === 'string') {
                      if (func51(data3) > 300) {
                        validate50.errors = [
                          {
                            instancePath: instancePath + '/recipients',
                            schemaPath: '#/properties/recipients/maxLength',
                            keyword: 'maxLength',
                            params: { limit: 300 },
                          },
                        ];
                        return false;
                      }
                    } else {
                      validate50.errors = [
                        {
                          instancePath: instancePath + '/recipients',
                          schemaPath: '#/properties/recipients/type',
                          keyword: 'type',
                          params: { type: 'string' },
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
                  if (data.date !== void 0 && func0.call(data, 'date')) {
                    let data4 = data.date;
                    const _errs11 = errors;
                    if (errors === _errs11) {
                      if (typeof data4 === 'string') {
                        if (func51(data4) > 20) {
                          validate50.errors = [
                            {
                              instancePath: instancePath + '/date',
                              schemaPath: '#/properties/date/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 20 },
                            },
                          ];
                          return false;
                        } else {
                          if (func51(data4) < 20) {
                            validate50.errors = [
                              {
                                instancePath: instancePath + '/date',
                                schemaPath: '#/properties/date/minLength',
                                keyword: 'minLength',
                                params: { limit: 20 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern29.test(data4)) {
                              validate50.errors = [
                                {
                                  instancePath: instancePath + '/date',
                                  schemaPath: '#/properties/date/pattern',
                                  keyword: 'pattern',
                                  params: { pattern: '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' },
                                },
                              ];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate50.errors = [
                          {
                            instancePath: instancePath + '/date',
                            schemaPath: '#/properties/date/type',
                            keyword: 'type',
                            params: { type: 'string' },
                          },
                        ];
                        return false;
                      }
                    }
                    var valid0 = _errs11 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.read !== void 0 && func0.call(data, 'read')) {
                      const _errs13 = errors;
                      if (typeof data.read !== 'boolean') {
                        validate50.errors = [
                          {
                            instancePath: instancePath + '/read',
                            schemaPath: '#/properties/read/type',
                            keyword: 'type',
                            params: { type: 'boolean' },
                          },
                        ];
                        return false;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.flagged !== void 0 && func0.call(data, 'flagged')) {
                        const _errs15 = errors;
                        if (typeof data.flagged !== 'boolean') {
                          validate50.errors = [
                            {
                              instancePath: instancePath + '/flagged',
                              schemaPath: '#/properties/flagged/type',
                              keyword: 'type',
                              params: { type: 'boolean' },
                            },
                          ];
                          return false;
                        }
                        var valid0 = _errs15 === errors;
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
      validate50.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate50.errors = vErrors;
  return errors === 0;
}
function validate49(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) ||
        ((data.messages === void 0 || !func0.call(data, 'messages')) && (missing0 = 'messages'))
      ) {
        validate49.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'kind' || key0 === 'messages' || key0 === 'cursor')) {
            validate49.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate49.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'messages')) {
              validate49.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema64.properties.kind.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.messages !== void 0 && func0.call(data, 'messages')) {
              let data1 = data.messages;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (
                      !validate50(data1[i0], {
                        instancePath: instancePath + '/messages/' + i0,
                        parentData: data1,
                        parentDataProperty: i0,
                        rootData,
                      })
                    ) {
                      vErrors = vErrors === null ? validate50.errors : vErrors.concat(validate50.errors);
                      errors = vErrors.length;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate49.errors = [
                    {
                      instancePath: instancePath + '/messages',
                      schemaPath: '#/properties/messages/type',
                      keyword: 'type',
                      params: { type: 'array' },
                    },
                  ];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.cursor !== void 0 && func0.call(data, 'cursor')) {
                let data3 = data.cursor;
                const _errs7 = errors;
                const _errs8 = errors;
                if (errors === _errs8) {
                  if (typeof data3 === 'string') {
                    if (func51(data3) > 22) {
                      validate49.errors = [
                        {
                          instancePath: instancePath + '/cursor',
                          schemaPath: '#/definitions/Handle/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 22 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data3) < 22) {
                        validate49.errors = [
                          {
                            instancePath: instancePath + '/cursor',
                            schemaPath: '#/definitions/Handle/minLength',
                            keyword: 'minLength',
                            params: { limit: 22 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern15.test(data3)) {
                          validate49.errors = [
                            {
                              instancePath: instancePath + '/cursor',
                              schemaPath: '#/definitions/Handle/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[A-Za-z0-9_-]{22}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate49.errors = [
                      {
                        instancePath: instancePath + '/cursor',
                        schemaPath: '#/definitions/Handle/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
      validate49.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate49.errors = vErrors;
  return errors === 0;
}
var schema69 = {
  type: 'object',
  additionalProperties: false,
  required: ['kind', 'code'],
  properties: { kind: { type: 'string', enum: ['error'] }, code: { $ref: '#/definitions/MailError' } },
};
var schema70 = {
  type: 'string',
  enum: ['invalid_request', 'stale_handle', 'stale_cursor', 'unsupported', 'busy', 'too_large', 'failed'],
};
function validate53(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) ||
        ((data.code === void 0 || !func0.call(data, 'code')) && (missing0 = 'code'))
      ) {
        validate53.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'kind' || key0 === 'code')) {
            validate53.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate53.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'error')) {
              validate53.errors = [
                {
                  instancePath: instancePath + '/kind',
                  schemaPath: '#/properties/kind/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema69.properties.kind.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.code !== void 0 && func0.call(data, 'code')) {
              let data1 = data.code;
              const _errs4 = errors;
              if (typeof data1 !== 'string') {
                validate53.errors = [
                  {
                    instancePath: instancePath + '/code',
                    schemaPath: '#/definitions/MailError/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  },
                ];
                return false;
              }
              if (!(
                data1 === 'invalid_request' ||
                data1 === 'stale_handle' ||
                data1 === 'stale_cursor' ||
                data1 === 'unsupported' ||
                data1 === 'busy' ||
                data1 === 'too_large' ||
                data1 === 'failed'
              )) {
                validate53.errors = [
                  {
                    instancePath: instancePath + '/code',
                    schemaPath: '#/definitions/MailError/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema70.enum },
                  },
                ];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate53.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate53.errors = vErrors;
  return errors === 0;
}
function validate38(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  const _errs0 = errors;
  let valid0 = false;
  let passing0 = null;
  const _errs1 = errors;
  if (!validate39(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate39.errors : vErrors.concat(validate39.errors);
    errors = vErrors.length;
  }
  var _valid0 = _errs1 === errors;
  if (_valid0) {
    valid0 = true;
    passing0 = 0;
  }
  const _errs2 = errors;
  if (!validate45(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate45.errors : vErrors.concat(validate45.errors);
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
    if (!validate49(data, { instancePath, parentData, parentDataProperty, rootData })) {
      vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
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
      const _errs5 = errors;
      if (errors === _errs5) {
        if (data && typeof data == 'object' && !Array.isArray(data)) {
          let missing0;
          if ((data.kind === void 0 || !func0.call(data, 'kind')) && (missing0 = 'kind')) {
            const err0 = {
              instancePath,
              schemaPath: '#/definitions/ClosedResult/required',
              keyword: 'required',
              params: { missingProperty: missing0 },
            };
            if (vErrors === null) {
              vErrors = [err0];
            } else {
              vErrors.push(err0);
            }
            errors++;
          } else {
            const _errs7 = errors;
            for (const key0 of Object.keys(data)) {
              if (!(key0 === 'kind')) {
                const err1 = {
                  instancePath,
                  schemaPath: '#/definitions/ClosedResult/additionalProperties',
                  keyword: 'additionalProperties',
                  params: { additionalProperty: key0 },
                };
                if (vErrors === null) {
                  vErrors = [err1];
                } else {
                  vErrors.push(err1);
                }
                errors++;
                break;
              }
            }
            if (_errs7 === errors) {
              if (data.kind !== void 0 && func0.call(data, 'kind')) {
                let data0 = data.kind;
                if (typeof data0 !== 'string') {
                  const err2 = {
                    instancePath: instancePath + '/kind',
                    schemaPath: '#/definitions/ClosedResult/properties/kind/type',
                    keyword: 'type',
                    params: { type: 'string' },
                  };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                }
                if (!(data0 === 'closed')) {
                  const err3 = {
                    instancePath: instancePath + '/kind',
                    schemaPath: '#/definitions/ClosedResult/properties/kind/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema68.properties.kind.enum },
                  };
                  if (vErrors === null) {
                    vErrors = [err3];
                  } else {
                    vErrors.push(err3);
                  }
                  errors++;
                }
              }
            }
          }
        } else {
          const err4 = {
            instancePath,
            schemaPath: '#/definitions/ClosedResult/type',
            keyword: 'type',
            params: { type: 'object' },
          };
          if (vErrors === null) {
            vErrors = [err4];
          } else {
            vErrors.push(err4);
          }
          errors++;
        }
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
        const _errs10 = errors;
        if (!validate53(data, { instancePath, parentData, parentDataProperty, rootData })) {
          vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
          errors = vErrors.length;
        }
        var _valid0 = _errs10 === errors;
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
    const err5 = { instancePath, schemaPath: '#/oneOf', keyword: 'oneOf', params: { passingSchemas: passing0 } };
    if (vErrors === null) {
      vErrors = [err5];
    } else {
      vErrors.push(err5);
    }
    errors++;
    validate38.errors = vErrors;
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
  validate38.errors = vErrors;
  return errors === 0;
}
function validate37(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.type === void 0 || !func0.call(data, 'type')) && (missing0 = 'type')) ||
        ((data.protocol_version === void 0 || !func0.call(data, 'protocol_version')) &&
          (missing0 = 'protocol_version')) ||
        ((data.generation === void 0 || !func0.call(data, 'generation')) && (missing0 = 'generation')) ||
        ((data.request_id === void 0 || !func0.call(data, 'request_id')) && (missing0 = 'request_id')) ||
        ((data.result === void 0 || !func0.call(data, 'result')) && (missing0 = 'result')) ||
        ((data.mac === void 0 || !func0.call(data, 'mac')) && (missing0 = 'mac'))
      ) {
        validate37.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(
            key0 === 'type' ||
            key0 === 'protocol_version' ||
            key0 === 'generation' ||
            key0 === 'request_id' ||
            key0 === 'result' ||
            key0 === 'mac'
          )) {
            validate37.errors = [
              {
                instancePath,
                schemaPath: '#/additionalProperties',
                keyword: 'additionalProperties',
                params: { additionalProperty: key0 },
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
              validate37.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'reply')) {
              validate37.errors = [
                {
                  instancePath: instancePath + '/type',
                  schemaPath: '#/properties/type/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema49.properties.type.enum },
                },
              ];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.protocol_version !== void 0 && func0.call(data, 'protocol_version')) {
              let data1 = data.protocol_version;
              const _errs4 = errors;
              if (!(typeof data1 == 'number' && !(data1 % 1) && !isNaN(data1) && isFinite(data1))) {
                validate37.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/type',
                    keyword: 'type',
                    params: { type: 'integer' },
                  },
                ];
                return false;
              }
              if (!(data1 === 2)) {
                validate37.errors = [
                  {
                    instancePath: instancePath + '/protocol_version',
                    schemaPath: '#/properties/protocol_version/enum',
                    keyword: 'enum',
                    params: { allowedValues: schema49.properties.protocol_version.enum },
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
                const _errs6 = errors;
                const _errs7 = errors;
                if (errors === _errs7) {
                  if (typeof data2 === 'string') {
                    if (func51(data2) > 32) {
                      validate37.errors = [
                        {
                          instancePath: instancePath + '/generation',
                          schemaPath: '#/definitions/Generation/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (func51(data2) < 32) {
                        validate37.errors = [
                          {
                            instancePath: instancePath + '/generation',
                            schemaPath: '#/definitions/Generation/minLength',
                            keyword: 'minLength',
                            params: { limit: 32 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern6.test(data2)) {
                          validate37.errors = [
                            {
                              instancePath: instancePath + '/generation',
                              schemaPath: '#/definitions/Generation/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[a-f0-9]{32}$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate37.errors = [
                      {
                        instancePath: instancePath + '/generation',
                        schemaPath: '#/definitions/Generation/type',
                        keyword: 'type',
                        params: { type: 'string' },
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
                if (data.request_id !== void 0 && func0.call(data, 'request_id')) {
                  let data3 = data.request_id;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (!(typeof data3 == 'number' && !(data3 % 1) && !isNaN(data3) && isFinite(data3))) {
                    validate37.errors = [
                      {
                        instancePath: instancePath + '/request_id',
                        schemaPath: '#/definitions/RequestId/type',
                        keyword: 'type',
                        params: { type: 'integer' },
                      },
                    ];
                    return false;
                  }
                  if (errors === _errs10) {
                    if (typeof data3 == 'number' && isFinite(data3)) {
                      if (data3 > 2147483647 || isNaN(data3)) {
                        validate37.errors = [
                          {
                            instancePath: instancePath + '/request_id',
                            schemaPath: '#/definitions/RequestId/maximum',
                            keyword: 'maximum',
                            params: { comparison: '<=', limit: 2147483647 },
                          },
                        ];
                        return false;
                      } else {
                        if (data3 < 1 || isNaN(data3)) {
                          validate37.errors = [
                            {
                              instancePath: instancePath + '/request_id',
                              schemaPath: '#/definitions/RequestId/minimum',
                              keyword: 'minimum',
                              params: { comparison: '>=', limit: 1 },
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
                if (valid0) {
                  if (data.result !== void 0 && func0.call(data, 'result')) {
                    const _errs12 = errors;
                    if (
                      !validate38(data.result, {
                        instancePath: instancePath + '/result',
                        parentData: data,
                        parentDataProperty: 'result',
                        rootData,
                      })
                    ) {
                      vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.mac !== void 0 && func0.call(data, 'mac')) {
                      let data5 = data.mac;
                      const _errs13 = errors;
                      const _errs14 = errors;
                      if (errors === _errs14) {
                        if (typeof data5 === 'string') {
                          if (func51(data5) > 64) {
                            validate37.errors = [
                              {
                                instancePath: instancePath + '/mac',
                                schemaPath: '#/definitions/Signature/maxLength',
                                keyword: 'maxLength',
                                params: { limit: 64 },
                              },
                            ];
                            return false;
                          } else {
                            if (func51(data5) < 64) {
                              validate37.errors = [
                                {
                                  instancePath: instancePath + '/mac',
                                  schemaPath: '#/definitions/Signature/minLength',
                                  keyword: 'minLength',
                                  params: { limit: 64 },
                                },
                              ];
                              return false;
                            } else {
                              if (!pattern0.test(data5)) {
                                validate37.errors = [
                                  {
                                    instancePath: instancePath + '/mac',
                                    schemaPath: '#/definitions/Signature/pattern',
                                    keyword: 'pattern',
                                    params: { pattern: '^[a-f0-9]{64}$' },
                                  },
                                ];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate37.errors = [
                            {
                              instancePath: instancePath + '/mac',
                              schemaPath: '#/definitions/Signature/type',
                              keyword: 'type',
                              params: { type: 'string' },
                            },
                          ];
                          return false;
                        }
                      }
                      var valid0 = _errs13 === errors;
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
      validate37.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate37.errors = vErrors;
  return errors === 0;
}
function validate10(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  const _errs0 = errors;
  let valid0 = false;
  let passing0 = null;
  const _errs1 = errors;
  if (!validate11(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate11.errors : vErrors.concat(validate11.errors);
    errors = vErrors.length;
  }
  var _valid0 = _errs1 === errors;
  if (_valid0) {
    valid0 = true;
    passing0 = 0;
  }
  const _errs2 = errors;
  if (!validate13(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate13.errors : vErrors.concat(validate13.errors);
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
    if (!validate15(data, { instancePath, parentData, parentDataProperty, rootData })) {
      vErrors = vErrors === null ? validate15.errors : vErrors.concat(validate15.errors);
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
      if (!validate17(data, { instancePath, parentData, parentDataProperty, rootData })) {
        vErrors = vErrors === null ? validate17.errors : vErrors.concat(validate17.errors);
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
        if (!validate19(data, { instancePath, parentData, parentDataProperty, rootData })) {
          vErrors = vErrors === null ? validate19.errors : vErrors.concat(validate19.errors);
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
          const _errs6 = errors;
          if (!validate21(data, { instancePath, parentData, parentDataProperty, rootData })) {
            vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
            errors = vErrors.length;
          }
          var _valid0 = _errs6 === errors;
          if (_valid0 && valid0) {
            valid0 = false;
            passing0 = [passing0, 5];
          } else {
            if (_valid0) {
              valid0 = true;
              passing0 = 5;
            }
            const _errs7 = errors;
            if (!validate23(data, { instancePath, parentData, parentDataProperty, rootData })) {
              vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
              errors = vErrors.length;
            }
            var _valid0 = _errs7 === errors;
            if (_valid0 && valid0) {
              valid0 = false;
              passing0 = [passing0, 6];
            } else {
              if (_valid0) {
                valid0 = true;
                passing0 = 6;
              }
              const _errs8 = errors;
              if (!validate35(data, { instancePath, parentData, parentDataProperty, rootData })) {
                vErrors = vErrors === null ? validate35.errors : vErrors.concat(validate35.errors);
                errors = vErrors.length;
              }
              var _valid0 = _errs8 === errors;
              if (_valid0 && valid0) {
                valid0 = false;
                passing0 = [passing0, 7];
              } else {
                if (_valid0) {
                  valid0 = true;
                  passing0 = 7;
                }
                const _errs9 = errors;
                if (!validate37(data, { instancePath, parentData, parentDataProperty, rootData })) {
                  vErrors = vErrors === null ? validate37.errors : vErrors.concat(validate37.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs9 === errors;
                if (_valid0 && valid0) {
                  valid0 = false;
                  passing0 = [passing0, 8];
                } else {
                  if (_valid0) {
                    valid0 = true;
                    passing0 = 8;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  if (!valid0) {
    const err0 = { instancePath, schemaPath: '#/oneOf', keyword: 'oneOf', params: { passingSchemas: passing0 } };
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
