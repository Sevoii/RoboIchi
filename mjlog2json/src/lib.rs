mod macros;
mod mjai_format;
mod tenhou_format;
mod xml_format;
mod xml_json_conv;

#[pyo3::pymodule]
mod mjlog2json {
    use crate::mjai_format;
    use crate::mjai_format::tenhou;
    use crate::tenhou_format::exporter::export_tenhou_json;
    use crate::tenhou_format::model::TenhouJson;
    use crate::xml_format::parser::parse_mjlogs;
    use crate::xml_json_conv::conv_to_tenhou_json;
    use pyo3::exceptions::PyRuntimeError;
    use pyo3::prelude::*;
    use std::error::Error;

    #[pyfunction]
    fn convert_xml_to_tenhou(content_xml: String) -> PyResult<String> {
        let mjlogs =
            parse_mjlogs(&content_xml).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let mjlog = &mjlogs[0];

        let converted =
            conv_to_tenhou_json(mjlog).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let json =
            export_tenhou_json(&converted).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(json)
    }

    #[pyfunction]
    fn convert_tenhou_to_mjai(tenhou: String) -> PyResult<String> {
        let log = tenhou::Log::from_json_str(&tenhou)
            .map_err(|e| PyRuntimeError::new_err(format!("{e:?}")))?;
        let res = mjai_format::tenhou_to_mjai(&log)
            .map_err(|e| PyRuntimeError::new_err(format!("{e:?}")))?;
        let json =
            serde_json::to_string(&res).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(json)
    }

    #[pyfunction]
    fn convert_xml_to_mjai(content_xml: String) -> PyResult<String> {
        let mjlogs =
            parse_mjlogs(&content_xml).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let mjlog = &mjlogs[0];

        let converted =
            conv_to_tenhou_json(mjlog).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let tenhou =
            export_tenhou_json(&converted).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let log = tenhou::Log::from_json_str(&tenhou)
            .map_err(|e| PyRuntimeError::new_err(format!("{e:?}")))?;
        let res = mjai_format::tenhou_to_mjai(&log)
            .map_err(|e| PyRuntimeError::new_err(format!("{e:?}")))?;
        let json =
            serde_json::to_string(&res).map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(json)
    }
}
