use std::fmt;

use serde::{
    Deserialize, Deserializer,
    de::{Error, MapAccess, SeqAccess, Visitor},
};
use serde_json::{Map, Number, Value};

use crate::ContractError;

struct UniqueValue(Value);

pub fn parse_message(raw: &str) -> Result<Value, ContractError> {
    serde_json::from_str::<UniqueValue>(raw)
        .map(|message| message.0)
        .map_err(|_| ContractError::InvalidMessage)
}

impl<'de> Deserialize<'de> for UniqueValue {
    fn deserialize<Decoder>(decoder: Decoder) -> Result<Self, Decoder::Error>
    where
        Decoder: Deserializer<'de>,
    {
        decoder.deserialize_any(UniqueValueVisitor)
    }
}

struct UniqueValueVisitor;

impl<'de> Visitor<'de> for UniqueValueVisitor {
    type Value = UniqueValue;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("JSON without duplicate object members")
    }

    fn visit_bool<Failure: Error>(self, value: bool) -> Result<Self::Value, Failure> {
        Ok(UniqueValue(Value::Bool(value)))
    }

    fn visit_i64<Failure: Error>(self, value: i64) -> Result<Self::Value, Failure> {
        Ok(UniqueValue(Value::Number(value.into())))
    }

    fn visit_u64<Failure: Error>(self, value: u64) -> Result<Self::Value, Failure> {
        Ok(UniqueValue(Value::Number(value.into())))
    }

    fn visit_f64<Failure: Error>(self, value: f64) -> Result<Self::Value, Failure> {
        Number::from_f64(value)
            .map(|number| UniqueValue(Value::Number(number)))
            .ok_or_else(|| Failure::custom("Invalid JSON number."))
    }

    fn visit_str<Failure: Error>(self, value: &str) -> Result<Self::Value, Failure> {
        Ok(UniqueValue(Value::String(value.to_owned())))
    }

    fn visit_unit<Failure: Error>(self) -> Result<Self::Value, Failure> {
        Ok(UniqueValue(Value::Null))
    }

    fn visit_seq<Sequence>(self, mut sequence: Sequence) -> Result<Self::Value, Sequence::Error>
    where
        Sequence: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element::<UniqueValue>()? {
            values.push(value.0);
        }
        Ok(UniqueValue(Value::Array(values)))
    }

    fn visit_map<Object>(self, mut object: Object) -> Result<Self::Value, Object::Error>
    where
        Object: MapAccess<'de>,
    {
        let mut properties = Map::new();
        while let Some(key) = object.next_key::<String>()? {
            if properties.contains_key(&key) {
                return Err(Object::Error::custom("Duplicate JSON object member."));
            }
            let value = object.next_value::<UniqueValue>()?;
            properties.insert(key, value.0);
        }
        Ok(UniqueValue(Value::Object(properties)))
    }
}
