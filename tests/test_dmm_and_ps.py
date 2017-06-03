from power_supply_agilent_e36xx import AgilentE36xxPowerSupply
from dmm_agilent_3446x import Agilent34461DMM


def main():
    import argparse
    # handle command-line args
    parser = argparse.ArgumentParser(description="test Agilent 34461 dmm and Agilent 3640 power supply drivers")
    parser.add_argument('dmm_visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the dmm you want to talk to. " +
                        "e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or DMM")
    parser.add_argument('ps_visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the power supply you want to talk to. " +
                        "e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or PS")
    parser.add_argument('--num_loops', '-n',
                        nargs=1,
                        default=[1],
                        type=int,
                        help="Number of times to loop test")

    ps_model = 'e3640a'

    args = parser.parse_args()
    # Trick to remember about argparse: if you have positional args, they get loaded into a list, even if only one.
    dmm_visa_alias = args.dmm_visa_alias[0]
    ps_visa_alias = args.ps_visa_alias[0]
    num_loops = args.num_loops[0]
    for iteration in range(0, num_loops):
        print "Iteration #" + str(iteration)
        print ("Instantiating Agilent34461 driver for device [{0}]...".format(dmm_visa_alias))
        dmm = Agilent34461DMM(dmm_visa_alias)

        print ("Instantiating Agilent3640 driver for device [{0}]...".format(ps_visa_alias))
        power_supply = AgilentE36xxPowerSupply(ps_visa_alias, ps_model)
        print("setting PS voltage to 5V with current limit of 0.5")
        power_supply.set_voltage(5)
        power_supply.set_current(0.5)
        print("Turning output on.")
        power_supply.output_on()

        print "measuring DMM current and voltage"
        print ("current: {0}".format(dmm.measure_current()))
        voltage = dmm.measure_voltage()
        print ("voltage: {0}".format(voltage))
        if (voltage < 4.95 or voltage > 5.05):
            print("voltage out of Bounds:" + str(voltage))
            raise Exception("Voltage out of Bounds")

        current = power_supply.measure_current()
        if(current >= .1 or current <= 0.09):
            print("Current out of Bounds:" + str(current))
            raise Exception("Current out of Bounds")

        print("Turning output off.")
        power_supply.output_off()
        print "Resetting..."
        dmm.reset()
        power_supply.reset()
        print "Running Self Test..."
        dmm.self_test()
        power_supply.self_test()

        power_supply.display_off()
        print "freeing DMM"
        dmm = None
        print "freeing PS"
        power_supply = None

if __name__ == '__main__':
    main()
