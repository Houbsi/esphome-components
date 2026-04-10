#pragma once

#include "esphome/core/component.h"
#include "esphome/components/fan/fan.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "../sec_touch.h"
#include "_fan_mode.h"

namespace esphome {
namespace sec_touch {

class SecTouchFan : public Component, public fan::Fan {
  static constexpr const char *TAG = "SecTouchFan";

 protected:
  const int level_id;
  const int label_id;
  SECTouchComponent *parent;
  void control(const fan::FanCall &call) override;
  static FanModeEnum::FanMode calculate_mode_from_speed(int speed);
  void update_label_mode();
  void turn_off_sec_touch_hardware_fan();
  /**
   * Will return `true` if an assignment was done so a call to publish is needed.
   */
  bool assign_new_speed_if_needed(int real_speed_from_device);

 public:
  SecTouchFan(SECTouchComponent *parent, int level_id, int label_id);

  void setup() override { this->set_supported_preset_modes(FanModeEnum::getPresetModePointers()); }
  // From Fan
  fan::FanTraits get_traits() override {
    auto traits = fan::FanTraits(false, true, false, 11);
    this->wire_preset_modes_(traits);
    return traits;
  }

  // Print method for debugging
  void dump_config() override;
};

}  // namespace sec_touch
}  // namespace esphome
