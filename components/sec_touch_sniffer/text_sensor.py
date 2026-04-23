import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text_sensor, switch
from esphome.components.time import RealTimeClock
from esphome.const import CONF_ID, CONF_TIME_ID

from esphome.components.sec_touch import CONF_SEC_TOUCH_ID, sec_touch_ns, SECTouchComponent

DEPENDENCIES = ["sec_touch"]
AUTO_LOAD = ["switch"]

CONF_SCAN_START = "scan_start"
CONF_SCAN_END = "scan_end"
CONF_SCAN_SWITCH = "scan_switch"

SecTouchSniffer = sec_touch_ns.class_(
    "SecTouchSniffer", cg.Component, text_sensor.TextSensor
)
SecTouchSnifferScanSwitch = sec_touch_ns.class_(
    "SecTouchSnifferScanSwitch", switch.Switch
)


def _validate_scan_range(config):
    if config.get(CONF_SCAN_END, 0) > 0:
        if config[CONF_SCAN_START] > config[CONF_SCAN_END]:
            raise cv.Invalid(
                f"scan_start ({config[CONF_SCAN_START]}) must be <= scan_end ({config[CONF_SCAN_END]})"
            )
    return config


CONFIG_SCHEMA = cv.All(
    text_sensor.text_sensor_schema(SecTouchSniffer)
    .extend(
        {
            cv.GenerateID(): cv.declare_id(SecTouchSniffer),
            cv.Required(CONF_SEC_TOUCH_ID): cv.use_id(SECTouchComponent),
            cv.Optional(CONF_TIME_ID): cv.use_id(RealTimeClock),
            cv.Optional(CONF_SCAN_START, default=1): cv.positive_int,
            cv.Optional(CONF_SCAN_END, default=0): cv.int_range(min=0),
            cv.Optional(CONF_SCAN_SWITCH): switch.switch_schema(SecTouchSnifferScanSwitch),
        }
    )
    .extend(cv.COMPONENT_SCHEMA),
    _validate_scan_range,
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_SEC_TOUCH_ID])
    var = cg.new_Pvariable(config[CONF_ID], parent)
    await cg.register_component(var, config)
    await text_sensor.register_text_sensor(var, config)

    if CONF_TIME_ID in config:
        time_var = await cg.get_variable(config[CONF_TIME_ID])
        cg.add(var.set_time(time_var))

    scan_end = config[CONF_SCAN_END]
    if scan_end > 0:
        cg.add(var.set_scan_range(config[CONF_SCAN_START], scan_end))

    if CONF_SCAN_SWITCH in config:
        sw = await switch.new_switch(config[CONF_SCAN_SWITCH])
        await cg.register_parented(sw, var)
        cg.add(var.set_scan_switch(sw))
