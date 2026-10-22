from TimeTagger import Coincidence, Coincidences, Combiner, Countrate, CoincidenceTimestamp, createTimeTagger
import elliptec
import numpy as np
import random
import time

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#    This is a python script designed to run the BB84 Protocol with
#    single heralded photons.
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

print("BB84 \n \n")

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                                 Inputs
#                               ++++++++++
#
#    The measurement duration for the time tagger is measured in 
#    picoseconds.
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

coincidenceWindow=10000
measurementDuration = 1e9
number_of_bits = 256

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                          Time Tagger Software 
#                        ++++++++++++++++++++++++
#
#      createTimeTagger() -- initializes the time tagger.
#       
#      Coincidences() -- takes input from the initialized time
#         tagger with the coincidences from [1, 2] and [1, 3] 
#         and a coincidenceWindow.
#  
#      coinc.getChannels() -- gets the channels from Coincidences()
#         and make them into an array that can then be called.
#         
#      rate = Countrate(tagger, [1, 2, coinc1_ch, coinc2_ch]) -- sets
#         up a measurement rate python array through the time tagger  
#         that takes in counts from channel 1, channel 2, and then 
#         the two coincidence measurements.
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

tagger = createTimeTagger()
coinc = Coincidences(tagger, [[1,2], [1,3]], coincidenceWindow, timestamp=CoincidenceTimestamp.ListedFirst)
coinc_chans = coinc.getChannels()
coinc1_ch = coinc_chans[0]  
coinc2_ch = coinc_chans[1]  
rate = Countrate(tagger, [1, 2, coinc1_ch, coinc2_ch])

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                 Elliptec Thorlabs Motor Control Software
#               ++++++++++++++++++++++++++++++++++++++++++++
#
#      controller = elliptec.Controller("COM4") -- connects through 
#         usb 'COM4' port to the motor mount.   
#       
#      elliptec.Rotator(controller) -- designates the controller as
#         a rotator.
#  
#      ro.home() -- sets polarization angle of the mount to the 
#         origin.
#
#      controller.close_connection() -- closes the controller 
#         connection. This is necessary to make sure the connection
#         to 'COM4' works on multiple iterations.
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

controller = elliptec.Controller('COM4')
ro = elliptec.Rotator(controller)
ro.home()
controller.close_connection()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                       Polarizations and Bits Arrays
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

polarizations = np.array([])
bits = np.array([])

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                                  Main
#                                ++++++++
#
#      For a given number of bits the outerwhile loop will iterate 
#      and rotate the half-wave plate motor mount to an angle of 
#      either 0, 45, 90, or 135.
#
#      The time tagger will be initialized within an inner while loop 
#      conditional to the number of coincidences observed between
#      channels 1 and 2 (counts[2]) or channels 1 and 3 (counts[3]).
#
#      If a coincidence of 1 is measured for counts[2], then a 0 is 
#      appended to the bit array. If a coincidence of 1 is measured
#      for counts[3], then a 1 is appended to the bit array. This
#      event represents the detection of a single 'heralded' photon.
#      The iteration variable i will then be increased by 1.
#
#      If the coincidences are measured to be 2 or greater for either
#      counts[2] or counts[3], then the inner while loop breaks, and
#      the outer while loop will not increase an iteration, thus 
#      redoing the measurement for that bit.
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

start_time = time.time()
elapsed_time = 0
i = 0

while i < number_of_bits:
    
    counts = [0., 0., 0., 0.]
    
    controller = elliptec.Controller('COM4')
    ro = elliptec.Rotator(controller)
    random_number = random.randint(0, 100)
    rand_mod_4 = random_number % 4
    pol_angle = rand_mod_4*45
    print(pol_angle)
    ro.set_angle(pol_angle)
    controller.close_connection()

    elapsed_time = time.time() - start_time

    while counts[2] < 2.0 and counts[3] < 2.0:
        print(f"Counts: {counts}")
        rate.startFor(measurementDuration, clear=True)
        rate.waitUntilFinished()
        counts += (rate.getData())/(1e3)
        print(f"Counts: {counts}")
        rate.stop()

        if counts[2] >= 2.0 and counts[3] >= 2.0:
            break
        if counts[2] == 1.0:
            bits = np.append(bits, 0)
            polarizations = np.append(polarizations, pol_angle)
            print(f"Bits: {bits}")
            i += 1
            break
        elif counts[3] == 1.0:
            bits = np.append(bits, 1)
            polarizations = np.append(polarizations, pol_angle)
            print(f"Bits: {bits}")
            i += 1
            break

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#                           Output and CSV File
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

print(f" \n \n ~~~ There were {len(bits)} bits created in {round(elapsed_time)} seconds. ~~~")
data = np.column_stack((bits, polarizations))
np.savetxt('bits.csv', data, delimiter=',')