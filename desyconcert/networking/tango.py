from concert.networking.base import get_tango_device


def get_p23_tango_device(uri):
    """Get a Tango device at ANKA's TopoTomo beam line specified by *uri*."""
    return get_tango_device(uri, peer="hasep23hika01:10000")
