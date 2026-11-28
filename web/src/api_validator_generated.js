// Generated from protocol/schema/api.schema.json.
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

// api_validator_generated.js
var validate = validate10;
var api_validator_generated_default = validate10;
var schema12 = {
  type: 'object',
  additionalProperties: false,
  required: ['authenticated'],
  properties: { authenticated: { type: 'boolean', enum: [true] } },
};
var func0 = Object.prototype.hasOwnProperty;
var schema14 = { type: 'string', enum: ['system', 'light', 'dark'] };
function validate11(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if ((data.theme === void 0 || !func0.call(data, 'theme')) && (missing0 = 'theme')) {
        validate11.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'theme')) {
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
          if (data.theme !== void 0 && func0.call(data, 'theme')) {
            let data0 = data.theme;
            if (typeof data0 !== 'string') {
              validate11.errors = [
                {
                  instancePath: instancePath + '/theme',
                  schemaPath: '#/definitions/Theme/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(data0 === 'system' || data0 === 'light' || data0 === 'dark')) {
              validate11.errors = [
                {
                  instancePath: instancePath + '/theme',
                  schemaPath: '#/definitions/Theme/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema14.enum },
                },
              ];
              return false;
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
var func55 = require_ucs2length().default;
var pattern0 = new RegExp('^[A-Za-z0-9._-]+$', 'u');
function validate15(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
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
        validate15.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'email')) {
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
          if (data.id !== void 0 && func0.call(data, 'id')) {
            let data0 = data.id;
            const _errs2 = errors;
            const _errs3 = errors;
            if (errors === _errs3) {
              if (typeof data0 === 'string') {
                if (func55(data0) > 128) {
                  validate15.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 128 },
                    },
                  ];
                  return false;
                } else {
                  if (func55(data0) < 1) {
                    validate15.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 1 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern0.test(data0)) {
                      validate15.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9._-]+$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate15.errors = [
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
                  if (func55(data1) > 128) {
                    validate15.errors = [
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
                  validate15.errors = [
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
                    if (func55(data2) > 254) {
                      validate15.errors = [
                        {
                          instancePath: instancePath + '/email',
                          schemaPath: '#/properties/email/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 254 },
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 1) {
                        validate15.errors = [
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
                    validate15.errors = [
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
      validate15.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate15.errors = vErrors;
  return errors === 0;
}
function validate14(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
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
        validate14.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'identities')) {
            validate14.errors = [
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
                if (func55(data0) > 128) {
                  validate14.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 128 },
                    },
                  ];
                  return false;
                } else {
                  if (func55(data0) < 1) {
                    validate14.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 1 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern0.test(data0)) {
                      validate14.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9._-]+$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate14.errors = [
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
                  if (func55(data1) > 128) {
                    validate14.errors = [
                      {
                        instancePath: instancePath + '/name',
                        schemaPath: '#/properties/name/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 128 },
                      },
                    ];
                    return false;
                  } else {
                    if (func55(data1) < 1) {
                      validate14.errors = [
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
                  validate14.errors = [
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
                        !validate15(data2[i0], {
                          instancePath: instancePath + '/identities/' + i0,
                          parentData: data2,
                          parentDataProperty: i0,
                          rootData,
                        })
                      ) {
                        vErrors = vErrors === null ? validate15.errors : vErrors.concat(validate15.errors);
                        errors = vErrors.length;
                      }
                      var valid2 = _errs9 === errors;
                      if (!valid2) {
                        break;
                      }
                    }
                  } else {
                    validate14.errors = [
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
      validate14.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate14.errors = vErrors;
  return errors === 0;
}
function validate13(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if ((data.accounts === void 0 || !func0.call(data, 'accounts')) && (missing0 = 'accounts')) {
        validate13.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'accounts')) {
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
          if (data.accounts !== void 0 && func0.call(data, 'accounts')) {
            let data0 = data.accounts;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (Array.isArray(data0)) {
                var valid1 = true;
                const len0 = data0.length;
                for (let i0 = 0; i0 < len0; i0++) {
                  const _errs4 = errors;
                  if (
                    !validate14(data0[i0], {
                      instancePath: instancePath + '/accounts/' + i0,
                      parentData: data0,
                      parentDataProperty: i0,
                      rootData,
                    })
                  ) {
                    vErrors = vErrors === null ? validate14.errors : vErrors.concat(validate14.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate13.errors = [
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
var schema24 = { type: 'string', enum: ['inbox', 'drafts', 'sent', 'trash', 'archive', 'junk', 'templates', 'outbox'] };
function validate20(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.id === void 0 || !func0.call(data, 'id')) && (missing0 = 'id')) ||
        ((data.name === void 0 || !func0.call(data, 'name')) && (missing0 = 'name'))
      ) {
        validate20.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'id' || key0 === 'name' || key0 === 'parent' || key0 === 'role')) {
            validate20.errors = [
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
                if (func55(data0) > 128) {
                  validate20.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 128 },
                    },
                  ];
                  return false;
                } else {
                  if (func55(data0) < 1) {
                    validate20.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 1 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern0.test(data0)) {
                      validate20.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9._-]+$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate20.errors = [
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
                  if (func55(data1) > 255) {
                    validate20.errors = [
                      {
                        instancePath: instancePath + '/name',
                        schemaPath: '#/properties/name/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 255 },
                      },
                    ];
                    return false;
                  } else {
                    if (func55(data1) < 1) {
                      validate20.errors = [
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
                  validate20.errors = [
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
                    if (func55(data2) > 128) {
                      validate20.errors = [
                        {
                          instancePath: instancePath + '/parent',
                          schemaPath: '#/definitions/Handle/maxLength',
                          keyword: 'maxLength',
                          params: { limit: 128 },
                        },
                      ];
                      return false;
                    } else {
                      if (func55(data2) < 1) {
                        validate20.errors = [
                          {
                            instancePath: instancePath + '/parent',
                            schemaPath: '#/definitions/Handle/minLength',
                            keyword: 'minLength',
                            params: { limit: 1 },
                          },
                        ];
                        return false;
                      } else {
                        if (!pattern0.test(data2)) {
                          validate20.errors = [
                            {
                              instancePath: instancePath + '/parent',
                              schemaPath: '#/definitions/Handle/pattern',
                              keyword: 'pattern',
                              params: { pattern: '^[A-Za-z0-9._-]+$' },
                            },
                          ];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate20.errors = [
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
                    validate20.errors = [
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
                    validate20.errors = [
                      {
                        instancePath: instancePath + '/role',
                        schemaPath: '#/definitions/MailboxRole/enum',
                        keyword: 'enum',
                        params: { allowedValues: schema24.enum },
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
      validate20.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate20.errors = vErrors;
  return errors === 0;
}
function validate19(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if (
        ((data.mailboxes === void 0 || !func0.call(data, 'mailboxes')) && (missing0 = 'mailboxes')) ||
        ((data.truncated === void 0 || !func0.call(data, 'truncated')) && (missing0 = 'truncated'))
      ) {
        validate19.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'mailboxes' || key0 === 'truncated')) {
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
          if (data.mailboxes !== void 0 && func0.call(data, 'mailboxes')) {
            let data0 = data.mailboxes;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (Array.isArray(data0)) {
                var valid1 = true;
                const len0 = data0.length;
                for (let i0 = 0; i0 < len0; i0++) {
                  const _errs4 = errors;
                  if (
                    !validate20(data0[i0], {
                      instancePath: instancePath + '/mailboxes/' + i0,
                      parentData: data0,
                      parentDataProperty: i0,
                      rootData,
                    })
                  ) {
                    vErrors = vErrors === null ? validate20.errors : vErrors.concat(validate20.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate19.errors = [
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
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.truncated !== void 0 && func0.call(data, 'truncated')) {
              const _errs5 = errors;
              if (typeof data.truncated !== 'boolean') {
                validate19.errors = [
                  {
                    instancePath: instancePath + '/truncated',
                    schemaPath: '#/properties/truncated/type',
                    keyword: 'type',
                    params: { type: 'boolean' },
                  },
                ];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
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
var pattern5 = new RegExp('^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$', 'u');
function validate24(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
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
        validate24.errors = [
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
            validate24.errors = [
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
                if (func55(data0) > 128) {
                  validate24.errors = [
                    {
                      instancePath: instancePath + '/id',
                      schemaPath: '#/definitions/Handle/maxLength',
                      keyword: 'maxLength',
                      params: { limit: 128 },
                    },
                  ];
                  return false;
                } else {
                  if (func55(data0) < 1) {
                    validate24.errors = [
                      {
                        instancePath: instancePath + '/id',
                        schemaPath: '#/definitions/Handle/minLength',
                        keyword: 'minLength',
                        params: { limit: 1 },
                      },
                    ];
                    return false;
                  } else {
                    if (!pattern0.test(data0)) {
                      validate24.errors = [
                        {
                          instancePath: instancePath + '/id',
                          schemaPath: '#/definitions/Handle/pattern',
                          keyword: 'pattern',
                          params: { pattern: '^[A-Za-z0-9._-]+$' },
                        },
                      ];
                      return false;
                    }
                  }
                }
              } else {
                validate24.errors = [
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
                  if (func55(data1) > 300) {
                    validate24.errors = [
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
                  validate24.errors = [
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
                    if (func55(data2) > 300) {
                      validate24.errors = [
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
                    validate24.errors = [
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
                      if (func55(data3) > 300) {
                        validate24.errors = [
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
                      validate24.errors = [
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
                        if (func55(data4) > 20) {
                          validate24.errors = [
                            {
                              instancePath: instancePath + '/date',
                              schemaPath: '#/properties/date/maxLength',
                              keyword: 'maxLength',
                              params: { limit: 20 },
                            },
                          ];
                          return false;
                        } else {
                          if (func55(data4) < 20) {
                            validate24.errors = [
                              {
                                instancePath: instancePath + '/date',
                                schemaPath: '#/properties/date/minLength',
                                keyword: 'minLength',
                                params: { limit: 20 },
                              },
                            ];
                            return false;
                          } else {
                            if (!pattern5.test(data4)) {
                              validate24.errors = [
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
                        validate24.errors = [
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
                        validate24.errors = [
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
                          validate24.errors = [
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
      validate24.errors = [{ instancePath, schemaPath: '#/type', keyword: 'type', params: { type: 'object' } }];
      return false;
    }
  }
  validate24.errors = vErrors;
  return errors === 0;
}
var pattern6 = new RegExp('^[a-f0-9]{32}$', 'u');
function validate23(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if ((data.messages === void 0 || !func0.call(data, 'messages')) && (missing0 = 'messages')) {
        validate23.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'messages' || key0 === 'cursor')) {
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
          if (data.messages !== void 0 && func0.call(data, 'messages')) {
            let data0 = data.messages;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (Array.isArray(data0)) {
                var valid1 = true;
                const len0 = data0.length;
                for (let i0 = 0; i0 < len0; i0++) {
                  const _errs4 = errors;
                  if (
                    !validate24(data0[i0], {
                      instancePath: instancePath + '/messages/' + i0,
                      parentData: data0,
                      parentDataProperty: i0,
                      rootData,
                    })
                  ) {
                    vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate23.errors = [
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
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.cursor !== void 0 && func0.call(data, 'cursor')) {
              let data2 = data.cursor;
              const _errs5 = errors;
              const _errs6 = errors;
              if (errors === _errs6) {
                if (typeof data2 === 'string') {
                  if (func55(data2) > 32) {
                    validate23.errors = [
                      {
                        instancePath: instancePath + '/cursor',
                        schemaPath: '#/definitions/Cursor/maxLength',
                        keyword: 'maxLength',
                        params: { limit: 32 },
                      },
                    ];
                    return false;
                  } else {
                    if (func55(data2) < 32) {
                      validate23.errors = [
                        {
                          instancePath: instancePath + '/cursor',
                          schemaPath: '#/definitions/Cursor/minLength',
                          keyword: 'minLength',
                          params: { limit: 32 },
                        },
                      ];
                      return false;
                    } else {
                      if (!pattern6.test(data2)) {
                        validate23.errors = [
                          {
                            instancePath: instancePath + '/cursor',
                            schemaPath: '#/definitions/Cursor/pattern',
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
                      instancePath: instancePath + '/cursor',
                      schemaPath: '#/definitions/Cursor/type',
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
var schema30 = {
  type: 'string',
  enum: [
    'unauthenticated',
    'forbidden_origin',
    'invalid_request',
    'rate_limited',
    'invalid_password',
    'login_unconfigured',
    'storage_unavailable',
    'backend_disconnected',
    'backend_busy',
    'backend_timeout',
    'stale_handle',
    'stale_cursor',
    'unsupported',
    'backend_failed',
  ],
};
function validate27(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
  let vErrors = null;
  let errors = 0;
  if (errors === 0) {
    if (data && typeof data == 'object' && !Array.isArray(data)) {
      let missing0;
      if ((data.error === void 0 || !func0.call(data, 'error')) && (missing0 = 'error')) {
        validate27.errors = [
          { instancePath, schemaPath: '#/required', keyword: 'required', params: { missingProperty: missing0 } },
        ];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 of Object.keys(data)) {
          if (!(key0 === 'error')) {
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
          if (data.error !== void 0 && func0.call(data, 'error')) {
            let data0 = data.error;
            if (typeof data0 !== 'string') {
              validate27.errors = [
                {
                  instancePath: instancePath + '/error',
                  schemaPath: '#/definitions/ApiError/type',
                  keyword: 'type',
                  params: { type: 'string' },
                },
              ];
              return false;
            }
            if (!(
              data0 === 'unauthenticated' ||
              data0 === 'forbidden_origin' ||
              data0 === 'invalid_request' ||
              data0 === 'rate_limited' ||
              data0 === 'invalid_password' ||
              data0 === 'login_unconfigured' ||
              data0 === 'storage_unavailable' ||
              data0 === 'backend_disconnected' ||
              data0 === 'backend_busy' ||
              data0 === 'backend_timeout' ||
              data0 === 'stale_handle' ||
              data0 === 'stale_cursor' ||
              data0 === 'unsupported' ||
              data0 === 'backend_failed'
            )) {
              validate27.errors = [
                {
                  instancePath: instancePath + '/error',
                  schemaPath: '#/definitions/ApiError/enum',
                  keyword: 'enum',
                  params: { allowedValues: schema30.enum },
                },
              ];
              return false;
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
function validate10(data, { instancePath = '', parentData, parentDataProperty, rootData = data } = {}) {
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
      if ((data.authenticated === void 0 || !func0.call(data, 'authenticated')) && (missing0 = 'authenticated')) {
        const err0 = {
          instancePath,
          schemaPath: '#/definitions/SessionDocument/required',
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
          if (!(key0 === 'authenticated')) {
            const err1 = {
              instancePath,
              schemaPath: '#/definitions/SessionDocument/additionalProperties',
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
          if (data.authenticated !== void 0 && func0.call(data, 'authenticated')) {
            let data0 = data.authenticated;
            if (typeof data0 !== 'boolean') {
              const err2 = {
                instancePath: instancePath + '/authenticated',
                schemaPath: '#/definitions/SessionDocument/properties/authenticated/type',
                keyword: 'type',
                params: { type: 'boolean' },
              };
              if (vErrors === null) {
                vErrors = [err2];
              } else {
                vErrors.push(err2);
              }
              errors++;
            }
            if (!(data0 === true)) {
              const err3 = {
                instancePath: instancePath + '/authenticated',
                schemaPath: '#/definitions/SessionDocument/properties/authenticated/enum',
                keyword: 'enum',
                params: { allowedValues: schema12.properties.authenticated.enum },
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
        schemaPath: '#/definitions/SessionDocument/type',
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
  if (!validate11(data, { instancePath, parentData, parentDataProperty, rootData })) {
    vErrors = vErrors === null ? validate11.errors : vErrors.concat(validate11.errors);
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
    if (!validate13(data, { instancePath, parentData, parentDataProperty, rootData })) {
      vErrors = vErrors === null ? validate13.errors : vErrors.concat(validate13.errors);
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
      if (!validate19(data, { instancePath, parentData, parentDataProperty, rootData })) {
        vErrors = vErrors === null ? validate19.errors : vErrors.concat(validate19.errors);
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
        if (!validate23(data, { instancePath, parentData, parentDataProperty, rootData })) {
          vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
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
          const _errs11 = errors;
          if (!validate27(data, { instancePath, parentData, parentDataProperty, rootData })) {
            vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
            errors = vErrors.length;
          }
          var _valid0 = _errs11 === errors;
          if (_valid0 && valid0) {
            valid0 = false;
            passing0 = [passing0, 5];
          } else {
            if (_valid0) {
              valid0 = true;
              passing0 = 5;
            }
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
export { api_validator_generated_default as default, validate };
