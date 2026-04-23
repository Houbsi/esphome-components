#pragma once

#include "esphome/components/switch/switch.h"
#include "esphome/core/helpers.h"
#include "sec_touch_sniffer.h"

namespace esphome {
namespace sec_touch {

class SecTouchSnifferScanSwitch : public switch_::Switch, public Parented<SecTouchSniffer> {
 public:
  SecTouchSnifferScanSwitch() = default;

 protected:
  void write_state(bool state) override {
    if (state != this->parent_->is_scanning()) {
      this->parent_->toggle_scan();
    }
  }
};

}  // namespace sec_touch
}  // namespace esphome
