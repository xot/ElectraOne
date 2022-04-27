# ElectrOne - init 
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#
#
from .ElectraOne import ElectraOne

def create_instance(c_instance):
    """ Creates and returns the ElectraOne script """
    return ElectraOne(c_instance)

# FIXME: copied from RemoteSL; not sure what this is needed for
# ALso: does this influence MIDI channel bug in Live.MidiMap.map_midi_cc ?
def get_capabilities():
    return {
     CONTROLLER_ID_KEY: controller_id(vendor_id=4661, product_ids=[11], model_name=u'ElectraOne XOT'),
     PORTS_KEY: [inport(props=[NOTES_CC, REMOTE]),
                 inport(props=[NOTES_CC, REMOTE, SCRIPT]),
                 outport(props=[NOTES_CC, SYNC]),
                 outport(props=[SCRIPT])]}
