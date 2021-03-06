from coreapi.codecs import default_decoders
from coreapi.compat import string_types
from coreapi.document import Document, Link
from coreapi.exceptions import LinkLookupError
from coreapi.transports import default_transports, determine_transport
import collections
import itypes


LinkAncestor = collections.namedtuple('LinkAncestor', ['document', 'keys'])


def _lookup_link(document, keys):
    """
    Validates that keys looking up a link are correct.

    Returns a two-tuple of (link, link_ancestors).
    """
    if not isinstance(keys, (list, tuple)):
        msg = "'keys' must be a list of strings or ints."
        raise TypeError(msg)
    if any([
        not isinstance(key, string_types) and not isinstance(key, int)
        for key in keys
    ]):
        raise TypeError("'keys' must be a list of strings or ints.")

    # Determine the link node being acted on, and its parent document.
    # 'node' is the link we're calling the action for.
    # 'document_keys' is the list of keys to the link's parent document.
    node = document
    link_ancestors = [LinkAncestor(document=document, keys=[])]
    for idx, key in enumerate(keys):
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
            msg = 'Index %s did not reference a link. Key %s was not found.'
            raise LinkLookupError(msg % (index_string, repr(key).strip('u')))
        if isinstance(node, Document):
            ancestor = LinkAncestor(document=node, keys=keys[:idx + 1])
            link_ancestors.append(ancestor)

    # Ensure that we've correctly indexed into a link.
    if not isinstance(node, Link):
        index_string = ''.join('[%s]' % repr(key).strip('u') for key in keys)
        msg = "Can only call 'action' on a Link. Index %s returned type '%s'."
        raise LinkLookupError(
            msg % (index_string, type(node).__name__)
        )

    return (node, link_ancestors)


class Client(itypes.Object):
    def __init__(self, decoders=None, transports=None):
        if decoders is None:
            decoders = default_decoders
        if transports is None:
            transports = default_transports
        self._decoders = itypes.List(decoders)
        self._transports = itypes.List(transports)

    @property
    def decoders(self):
        return self._decoders

    @property
    def transports(self):
        return self._transports

    def get(self, url):
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(link.url, transports=self.transports)
        return transport.transition(link, decoders=self.decoders)

    def reload(self, document):
        url = document.url
        link = Link(url, action='get')

        # Perform the action, and return a new document.
        transport = determine_transport(link.url, transports=self.transports)
        return transport.transition(link, decoders=self.decoders)

    def action(self, document, keys, params=None, action=None, inplace=None):
        if isinstance(keys, string_types):
            keys = [keys]

        # Validate the keys and link parameters.
        link, link_ancestors = _lookup_link(document, keys)

        if (action is not None) or (inplace is not None):
            # Handle any explicit overrides.
            action = link.action if (action is None) else action
            inplace = link.inplace if (inplace is None) else inplace
            link = Link(link.url, action, inplace, link.fields)

        # Perform the action, and return a new document.
        transport = determine_transport(link.url, transports=self.transports)
        return transport.transition(link, params, decoders=self.decoders, link_ancestors=link_ancestors)
