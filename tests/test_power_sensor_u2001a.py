from usb_power_sensor_keysight_u2001a import KeysightU2001aPowerSensor
import argparse

def main():
    parser = argparse.ArgumentParser(description="test Keysight U2001a Power Sensor driver")
    parser.add_argument('visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the dmm you want to talk to. " +
                        "e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or PWR_SENSOR")
    parser.add_argument('--num_loops', '-n',
                        nargs=1,
                        default=[1],
                        type=int,
                        help="Number of times to loop test")

    args = parser.parse_args()
    pwr_sensor_visa_alias = args.pwr_sensor_visa_alias[0]
    num_loops = args.num_loops[0]

    for iteration in range(0, num_loops):
        print "Iteration #" + str(iteration)
        print ("Instantiating KeysightU2001a driver for device [{0}]...".format(pwr_sensor_visa_alias))
        pwr_sensor = KeysightU2001aPowerSensor(pwr_sensor_visa_alias)

        #print ("current: {0}".format(dmm.measure_current()))
        #print ("voltage: {0}".format(dmm.measure_voltage()))

        print "Resetting..."
        pwr_sensor.reset()
        print "Running Self Test..."
        pwr_sensor.self_test()
        print "Freeing Power Sensor..."
        pwr_sensor = None


if __name__ == '__main__':
    main()
