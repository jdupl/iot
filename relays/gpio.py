class Pin():
    def __init__(self, pin_id, gpio_wrapper, user_override=False):
        self.pin_id = pin_id
        self.state_str = 'off'
        self.on_user_override = user_override

    def __eq__(self, o):
        return self.pin_id == o.pin_id and \
            self.state_str == o.state_str

    def reset_user_override(self):
        # TODO trigger control relay routine
        self.on_user_override = False

    def as_pub_dict(self):
        return {
            'pin_id': self.pin_id,
            'state_str': self.state_str,
            'on_user_override': self.on_user_override
        }


class AbstractPhysicalGPIO():

    def setup(self, pin_id, gpio_value_init):
        raise Exception('Abstract method')

    def output(self, pin_id, gpio_value):
        self.GPIO.output(pin_id, gpio_value)

    def cleanup(self):
        pass

    def setup_pin(self, pin_id):
        pass

    def apply_state(self, pin_id, state_str):
        pass

    def set_user_override(self, pin, state_str):
        pin.on_user_override = True
        self.apply_state(pin.pin_id, state_str)


class RPiGPIOWrapper(AbstractPhysicalGPIO):
    # Implementation for Raspberry pi 1 to 3
    # Pin ID are BCM numbering
    def __init__(self):
        import RPi.GPIO as _GPIO
        self.GPIO = _GPIO
        self.GPIO.setwarnings(False)
        self.GPIO.setmode(_GPIO.BCM)

    def setup(self, pin_id, gpio_value_init):
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

    def setup(self, pin_id, gpio_value_init):
        self.pin_id = self.__get_addr_from_phy(pin_id)
        self.GPIO.setcfg(self.pin_id, self.GPIO.OUTPUT)
        self.GPIO.output(self.pin_id, gpio_value_init)

    def setup_pin(self, pin_id):
        self.GPIO.setup(pin_id, 1)

    def apply_state(self, pin_id, state_str):
        # 'on' is 0 on for a normally closed relay
        gpio_val = 0 if state_str == 'off' else 1
        try:
            addr = self.__get_addr_from_phy(pin_id)
            self.GPIO.output(addr, gpio_val)

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

    def setup(self, pin_id, gpio_value_init):
        print('Setting pin %d as output with value %s'
              % (pin_id, gpio_value_init))

    def output(self, pin_id, gpio_value):
        print('Setting pin %d as value %s' % (pin_id, gpio_value))
