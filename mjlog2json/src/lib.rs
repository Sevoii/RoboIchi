pub mod api;
mod macros;
mod mjai_format;
mod tenhou_format;
mod xml_format;
mod xml_json_conv;

pub use mjai_format::Event;

#[pyo3::pymodule]
mod mjlog2json {
    use anyhow::Result;
    use pyo3::prelude::*;
    use std::error::Error;

    #[pyfunction]
    fn convert_xml_to_tenhou(content_xml: String) -> Result<String> {
        crate::api::convert_xml_to_tenhou(content_xml)
    }

    #[pyfunction]
    fn convert_tenhou_to_mjai(tenhou: String) -> Result<String> {
        crate::api::convert_tenhou_to_mjai(tenhou)
    }

    #[pyfunction]
    fn convert_xml_to_mjai(content_xml: String) -> Result<String> {
        crate::api::convert_xml_to_mjai(content_xml)
    }
}
