class AbstractPhysicalGPIO():

    setup_pins = []  # store pins that are already setup

    def setup(self, pin_id, gpio_value_init):
        if pin_id not in self.setup_pins:
            self.setup_pins.append(pin_id)
            self._setup(pin_id, gpio_value_init)

    def output(self, pin_id, gpio_value):
        self.GPIO.output(pin_id, gpio_value)

    def cleanup(self):
        pass

    def setup_pin(self, pin_id):
        pass

    def apply_state(self, pin_id, state_str):
        pass

    def set_user_override(self, state_str):
        self.on_user_override = True
        self.apply_state(state_str)


class RPiGPIOWrapper(AbstractPhysicalGPIO):
    # Implementation for Raspberry pi 1 to 3
    # Pin ID are BCM numbering
    def __init__(self):
        import RPi.GPIO as _GPIO
        self.GPIO = _GPIO
        self.GPIO.setwarnings(False)
        self.GPIO.setmode(_GPIO.BCM)

    def _setup(self, pin_id, gpio_value_init):
        self.GPIO.setup(pin_id, self.GPIO.OUT, initial=gpio_value_init)

    def cleanup(self):
        self.GPIO.cleanup()


class OPiGPIOWrapper(AbstractPhysicalGPIO):
    # Implementation for Orange pi one
    # Pin ID are physical numbering
    def __init__(self):
        from pyA20.gpio import gpio as _GPIO
        from pyA20.gpio import connector as _connector

        self.GPIO = _GPIO
        self.GPIO.init()
        self.connector = _connector

    def _setup(self, pin_id, gpio_value_init):
        self.pin_id = self.__get_addr_from_phy(pin_id)
        self.GPIO.setcfg(self.pin_id, self.GPIO.OUTPUT)
        self.GPIO.output(self.pin_id, gpio_value_init)

    def setup_pin(self, pin_id):
        self.GPIO.setup(pin_id, 1)

    def apply_state(self, pin_id, state_str):
        # 'on' is 0 on for a normally closed relay
        gpio_val = 1 if state_str == 'off' else 0
        try:
            self.GPIO.output(pin_id, gpio_val)

            self.state_str = state_str
            print('Pin %d is now %s (%d)' % (pin_id,
                                             state_str, gpio_val))
        except Exception as e:
            print('Problem while changing pin %d status: '
                  % pin_id, e)

    def __get_addr_from_phy(self, pin_id):
        try:
            attr_name = 'gpio1p%d' % pin_id
            return getattr(self.connector, attr_name)
        except Exception as e:
            print(e)

    def cleanup(self):
        pass


class GPIOPrintWrapper(AbstractPhysicalGPIO):

    def _setup(self, pin_id, gpio_value_init):
        print('Setting pin %d as output with value %s'
              % (pin_id, gpio_value_init))

    def output(self, pin_id, gpio_value):
        print('Setting pin %d as value %s' % (pin_id, gpio_value))
