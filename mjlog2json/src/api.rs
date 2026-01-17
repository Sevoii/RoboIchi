use crate::mjai_format;
use crate::mjai_format::tenhou;
use crate::tenhou_format::exporter::export_tenhou_json;
use crate::xml_format::parser::{parse_mjlogs};
use crate::xml_json_conv::{conv_to_tenhou_json};
use anyhow::Result;


pub fn convert_xml_to_tenhou(content_xml: String) -> Result<String> {
    let mjlogs = parse_mjlogs(&content_xml)?;
    let mjlog = &mjlogs[0];

    let converted = conv_to_tenhou_json(mjlog)?;
    let json = export_tenhou_json(&converted)?;

    Ok(json)
}

pub fn convert_tenhou_to_mjai(tenhou: String) -> Result<String> {
    let log = tenhou::Log::from_json_str(&tenhou)?;
    let res = mjai_format::tenhou_to_mjai(&log)?;
    let json = serde_json::to_string(&res)?;

    Ok(json)
}

pub fn convert_xml_to_mjai(content_xml: String) -> Result<String> {
    let mjlogs = parse_mjlogs(&content_xml)?;
    let mjlog = &mjlogs[0];
    let converted = conv_to_tenhou_json(mjlog)?;
    let tenhou = export_tenhou_json(&converted)?;
    let log = tenhou::Log::from_json_str(&tenhou)?;
    let res = mjai_format::tenhou_to_mjai(&log)?;
    let json = serde_json::to_string(&res)?;

    Ok(json)
}

