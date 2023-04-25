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
    """ Creates and returns the ElectraOne script. (See DOCUMENTATION.md for
       details of the interfaces.)
        - c_instance: object exposing the interface to Live, ie functions
             that can be called to tell Live to do something.
        - result: the remote script object, whose functions Live can call
             to tell it to do something.
    """
    return ElectraOne(c_instance)

# TODO: copied from RemoteSL; not sure what this is needed for
def get_capabilities():
    return {
     CONTROLLER_ID_KEY: controller_id(vendor_id=4661, product_ids=[11], model_name=u'ElectraOne XOT'),
     PORTS_KEY: [inport(props=[NOTES_CC, REMOTE]),
                 inport(props=[NOTES_CC, REMOTE, SCRIPT]),
                 outport(props=[NOTES_CC, SYNC]),
                 outport(props=[SCRIPT])]
    }

# Push2
#def get_capabilities():
#    from ableton.v2.control_surface import capabilities as caps
#    return {caps.CONTROLLER_ID_KEY: caps.controller_id(vendor_id=10626, product_ids=[6503], model_name=u'Ableton Push 2'),
#     caps.PORTS_KEY: [caps.inport(props=[caps.HIDDEN, caps.NOTES_CC, caps.SCRIPT]),
#                      caps.inport(props=[]),
#                      caps.outport(props=[caps.HIDDEN,
#                       caps.NOTES_CC,
#                       caps.SYNC,
#                       caps.SCRIPT]),
#                      caps.outport(props=[])],
#     caps.TYPE_KEY: u'push2',
#     caps.AUTO_LOAD_KEY: True}
