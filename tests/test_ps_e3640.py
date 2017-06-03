from power_supply_agilent_e36xx import AgilentE36xxPowerSupply
import argparse


def main():
    parser = argparse.ArgumentParser(description="test Agilent 3640 power supply driver")
    parser.add_argument('ps_visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the power supply you want to talk to. " +
                        "e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or PS")
    parser.add_argument('--num_loops', '-n',
                        nargs=1,
                        default=[1],
                        type=int,
                        help="Number of times to loop test")

    args = parser.parse_args()
    ps_visa_alias = args.ps_visa_alias[0]
    num_loops = args.num_loops[0]
    ps_model = 'e3640a'

    for iteration in range(0, num_loops):
        print "Iteration #" + str(iteration)
        print("Instantiating AgilentE3640PowerSupply driver for device [{0}]...".format(ps_visa_alias))
        power_supply = AgilentE36xxPowerSupply(ps_visa_alias, ps_model)
        print("Setting voltage to 5V with current limit of 0.5A")
        power_supply.set_voltage(5)
        power_supply.set_current_limit(0.5)
        print("Turning output on.")
        power_supply.output_on()
        print("Turning output off.")
        power_supply.output_off()
        print("Turning output on.")
        power_supply.output_on()
        print("Measuring current.")
        current = power_supply.measure_current()
        if(current >= .1 or current <= 0.09):
            print("Current out of Bounds:" + str(current))
            raise Exception("Current out of Bounds")
        print "Measured Current: " + str(current)
        print("Measuring voltage.")
        print power_supply.measure_voltage()
        print("Turning off display.")
        power_supply.display_off()
        print("Resetting.")
        power_supply.reset()
        print("Performing self test.")
        power_supply.self_test()
        print("Releasing power supply.")
        power_supply = None


if __name__ == '__main__':
    main()
