use serde_json::Value;

pub fn canonical_json(message: &Value) -> String {
    let mut output = String::new();
    match message {
        Value::Object(properties) => write_object(
            properties.iter().filter(|(name, _)| name.as_str() != "mac"),
            &mut output,
        ),
        value => write_value(value, &mut output),
    }
    output
}

fn write_value(value: &Value, output: &mut String) {
    match value {
        Value::Object(properties) => write_object(properties.iter(), output),
        Value::Array(values) => {
            output.push('[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                write_value(value, output);
            }
            output.push(']');
        }
        scalar => output.push_str(&scalar.to_string()),
    }
}

fn write_object<'message>(properties: impl Iterator<Item = (&'message String, &'message Value)>, output: &mut String) {
    let mut properties: Vec<_> = properties.collect();
    properties.sort_unstable_by(|left, right| left.0.cmp(right.0));
    output.push('{');
    for (index, (name, value)) in properties.into_iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        output.push_str(&Value::String(name.clone()).to_string());
        output.push(':');
        write_value(value, output);
    }
    output.push('}');
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::canonical_json;

    #[test]
    fn a_non_object_root_keeps_its_members_and_sorts_nested_objects() {
        assert_eq!(
            canonical_json(&json!([{"mac": 1, "b": 2, "a": 3}, "x"])),
            r#"[{"a":3,"b":2,"mac":1},"x"]"#
        );
    }
}
