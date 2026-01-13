mod converter;
mod json_calc;
mod json_exporter;
mod json_model;
mod json_parser;
mod json_score;
mod xml_json_conv;
mod xml_model;
mod xml_parser;

#[pyo3::pymodule]
mod mjlog2json {
    use crate::json_exporter::export_tenhou_json;
    use crate::json_model::TenhouJson;
    use crate::xml_json_conv::conv_to_tenhou_json;
    use crate::xml_parser::parse_mjlogs;
    use pyo3::exceptions::PyRuntimeError;
    use pyo3::prelude::*;
    use std::error::Error;

    #[pyfunction]
    fn convert_log(content_xml: String, reference: String) -> PyResult<String> {
        let mjlogs = parse_mjlogs(&content_xml)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let mjlog = &mjlogs[0];

        let converted = conv_to_tenhou_json(mjlog)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let converted_tenhou_json = TenhouJson {
            reference,
            ..converted
        };


        let json = export_tenhou_json(&converted_tenhou_json)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(json)
    }
}
