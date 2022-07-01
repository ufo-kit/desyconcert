"""
Tango motors with DESY specific interfaces.
"""
import asyncio
import logging
from concert.helpers import memoize
from concert.devices.motors import base
from concert.base import HardLimitError

LOG = logging.getLogger(__name__)

try:
    import PyTango
except ImportError:
    LOG.warn("PyTango is not installed.")


TANGO_SLEEP_TIME = 0.1


class _TangoMixin(object):
    async def __ainit__(self, device):
        self._device = device
        self['position']._external_lower_getter = self._get_lower_external_position_limit
        self['position']._external_upper_getter = self._get_upper_external_position_limit

    async def _in_hard_limit(self):
        in_backward = (await self._device['CwLimit']).value
        in_forward = (await self._device['CcwLimit']).value

        return in_backward or in_forward

    async def _get_external_limit(self, which):
        return (await self._device[which]).value * self['position'].unit

    @memoize
    async def _get_upper_external_position_limit(self):
        return await self._get_external_limit("UnitLimitMax")

    @memoize
    async def _get_lower_external_position_limit(self):
        return await self._get_external_limit("UnitLimitMin")

    async def _get_state(self):
        if await self._in_hard_limit():
            return 'hard-limit'

        tango_state = await self._device.state()
        if tango_state == PyTango.DevState.MOVING:
            state = 'moving'
        elif tango_state in [PyTango.DevState.ON, PyTango.DevState.STANDBY]:
            state = 'standby'
        elif tango_state == PyTango.DevState.FAULT:
            state = 'fault'
        elif tango_state == PyTango.DevState.DISABLE:
            state = 'disabled'
        elif tango_state == PyTango.DevState.ALARM:
            state = 'alarm'
        else:
            raise ValueError("Unknown Tango state '{}'".format(tango_state))

        return state

    async def _wait_for_stop(self):
        await asyncio.sleep(TANGO_SLEEP_TIME)

        while True:
            if await self.get_state() == "moving":
                await asyncio.sleep(TANGO_SLEEP_TIME)
            else:
                break

    async def _stop(self):
        await self._device.StopMove()
        await self._wait_for_stop()

    async def _home(self):
        try:
            await self._device.MoveHome()
            await self._wait_for_stop()
        except asyncio.CancelledError:
            await self.stop()
            raise

    async def _get_position(self):
        return (await self._device['position']).value * self['position'].unit

    async def _set_position(self, position):
        try:
            await self._device.write_attribute('position',
                                               position.to(self['position'].unit).magnitude)
            await self._wait_for_stop()
            if await self._in_hard_limit():
                raise HardLimitError()
        except asyncio.CancelledError:
            await self.stop()
            raise

    async def __aenter__(self):
        self._device.lock()
        await self._lock.acquire()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._device.unlock()
        self._lock.release()


class LinearMotor(_TangoMixin, base.LinearMotor):
    """A linear motor based on DESY Tango motor interface."""

    async def __ainit__(self, tango_device):
        await base.LinearMotor.__ainit__(self)
        await _TangoMixin.__ainit__(self, tango_device)


class RotationMotor(_TangoMixin, base.RotationMotor):
    """A rotation motor based on DESY Tango motor interface."""

    async def __ainit__(self, tango_device):
        await base.RotationMotor.__ainit__(self)
        await _TangoMixin.__ainit__(self, tango_device)
