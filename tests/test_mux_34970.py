from mux_agilent_3497x import Agilent34970Mux
import argparse


def main():
    parser = argparse.ArgumentParser(description="test Agilent34970Mux driver")
    parser.add_argument('visa_alias',
                        nargs=1,
                        help="Visa resource descriptor (or alias) of the instrument you want to talk to." +
                        " e.g.USB0::0x0957::0x1A07::MY53204664::INSTR or MUX")
    parser.add_argument('--num_loops', '-n',
                        nargs=1,
                        default=[1],
                        type=int,
                        help="Number of times to loop test")

    args = parser.parse_args()
    visa_alias = args.visa_alias[0]
    num_loops = args.num_loops[0]

    for iteration in range(0, num_loops):
        print "Iteration #" + str(iteration)
        print ("Instantiating Agilent34970mux driver for device [{0}]...".format(visa_alias))
        mux = Agilent34970Mux(visa_alias)

        mux.clear_error_stack()

        print "vdd: {0}".format(mux.r4_hack_take_single_measurement_vdd())
        mux.clear_error_stack()
        print "Isupply: {0}".format(mux.r4_hack_take_single_measurement_i_supply())
        mux.clear_error_stack()
        print "Releasing mux"
        mux = None

if __name__ == '__main__':
    main()
