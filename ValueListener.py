# ValueListener
# - Listen to value changes and send value updates to E1
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#


class ValueListener:

    def __init__(self, parameter, info, base):
        """Add a value listener for the registered parameter that will send the
           new value of the parameter as a string (as formatted by Live) to the control on
           the E1 that controls it whenever it changes (or when update_value is called)
           - parameter: the parameter to add the value listener to; Live.DeviceParameter.DeviceParameter
           - info: info about the control on the E1
           - base: link to instance of ElectraOneBase (that is responsible
               for communicating with Live and the E1).
        """
        self._parameter = parameter
        self._controller = None # tbd based on info
        self._base = base
        self._base.debug(5,f'Adding listener for {self._parameter.original_name}.')
        self._parameter.add_value_listener(self.update_value)


    def remove(self):
        """Remove the value listeners for the registered parameter.
        """
        if self._parameter.value_has_listener(self.update_value):
            self._parameter.remove_value_listener(self.update_value)        

    def update_value(self):
        """Send a value update to the E1 for the registered parameter.
        """
        self._base.debug(5,f'Value of {self._parameter.original_name} changed to {str(self._parameter)}.')
        # ONLY SEND VALUE WHEN DEVICE IS VISIBLE!
        # self._base.send_value_update(self._controller,str(self._parameter))



        
class ValueListeners:
    """Maintain a list of value listeners for a device or a track.
    """

    def __init__(self, base):
        """Create an empty value listener list.
           - base: link to instance of ElectraOneBase (that is responsible
               for communicating with Live and the E1).
        """
        self._base = base
        self._listeners = []

    def add(self,parameter, info):
        """Add a value listener for a parameter that will send the new value of
           the parameter as a string (as formatted by Live) to the control on
           the E1 that controls it  whenever it changes (or when update_all is called).
           - parameter: the parameter to add the value listener to; Live.DeviceParameter.DeviceParameter
           - info: info about the control on the E1
        """
        listener = ValueListener(parameter, info, self._base)
        self._listeners.append(listener)

    def remove_all(self):
        """Remove all value listeners for all registered parameters in the list. 
        """
        for listener in self._listeners:
            listener.remove()

    def update_all(self):
        """Send a value update to the E1 for all registered parameters in the list. 
        """
        for listener in self._listeners:
            listener.update_value()
            
