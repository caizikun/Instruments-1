from dmm_agilent_3446x import Agilent34461DMM
import argparse


def main():
    parser = argparse.ArgumentParser(description="test Agilent 34461 dmm driver")
    parser.add_argument('dmm_visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the dmm you want to talk to. " +
                        "e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or DMM")
    parser.add_argument('--num_loops', '-n',
                        nargs=1,
                        default=[1],
                        type=int,
                        help="Number of times to loop test")

    args = parser.parse_args()
    dmm_visa_alias = args.dmm_visa_alias[0]
    num_loops = args.num_loops[0]

    for iteration in range(0, num_loops):
        print "Iteration #" + str(iteration)
        print ("Instantiating Agilent34461 driver for device [{0}]...".format(dmm_visa_alias))
        dmm = Agilent34461DMM(dmm_visa_alias)

        print ("current: {0}".format(dmm.measure_current()))
        print ("voltage: {0}".format(dmm.measure_voltage()))

        print "Resetting..."
        dmm.reset()
        print "Running Self Test..."
        dmm.self_test()
        print "Freeing DMM..."
        dmm = None


if __name__ == '__main__':
    main()
