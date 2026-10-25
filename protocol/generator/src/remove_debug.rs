use syn::{Attribute, Path, Token, punctuated::Punctuated, visit_mut::VisitMut};

pub struct RemoveDebug;

impl VisitMut for RemoveDebug {
    fn visit_item_mod_mut(&mut self, module: &mut syn::ItemMod) {
        if module.ident != "error" {
            syn::visit_mut::visit_item_mod_mut(self, module);
        }
    }

    fn visit_attribute_mut(&mut self, attribute: &mut Attribute) {
        if attribute.path().is_ident("derive") {
            let mut derives = attribute
                .parse_args_with(Punctuated::<Path, Token![,]>::parse_terminated)
                .expect("Typify emits valid derive attributes.");
            derives = derives
                .into_iter()
                .filter(|path| {
                    path.segments
                        .last()
                        .is_none_or(|segment| segment.ident != "Debug")
                })
                .collect();
            *attribute = syn::parse_quote!(#[derive(#derives)]);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::RemoveDebug;
    use syn::visit_mut::VisitMut;

    #[test]
    fn wire_types_cannot_derive_debug_but_errors_can() {
        let mut syntax = syn::parse_quote! {
            #[derive(Clone, Debug)]
            struct Authenticate { token: String }
            mod error {
                #[derive(Debug)]
                struct ConversionError;
            }
        };
        RemoveDebug.visit_file_mut(&mut syntax);
        let source = prettyplease::unparse(&syntax);
        assert!(source.starts_with("#[derive(Clone)]"));
        assert_eq!(source.matches("derive(Debug)").count(), 1);
    }
}
