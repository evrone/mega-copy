import copy
from dataclasses import _is_dataclass_instance, fields

dict_factory = lambda d: {
    f"{k}_param" if k == "type" else k: v for k, v in dict(d).items()
}


def serialize_dc(obj, *args):
    if _is_dataclass_instance(obj):
        result = []
        for f in fields(obj):
            value = serialize_dc(getattr(obj, f.name), dict_factory)
            result.append((f.name, value))
        return {**dict_factory(result), "type": obj.__class__.__name__}
    elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
        # obj is a namedtuple.  Recurse into it, but the returned
        # object is another namedtuple of the same type.  This is
        # similar to how other list- or tuple-derived classes are
        # treated (see below), but we just need to create them
        # differently because a namedtuple's __init__ needs to be
        # called differently (see bpo-34363).

        # I'm not using namedtuple's _asdict()
        # method, because:
        # - it does not recurse in to the namedtuple fields and
        #   convert them to dicts (using dict_factory).
        # - I don't actually want to return a dict here.  The main
        #   use case here is json.dumps, and it handles converting
        #   namedtuples to lists.  Admittedly we're losing some
        #   information here when we produce a json list instead of a
        #   dict.  Note that if we returned dicts here instead of
        #   namedtuples, we could no longer call asdict() on a data
        #   structure where a namedtuple was used as a dict key.

        return type(obj)(*[serialize_dc(v, dict_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        # Assume we can create an object of this type by passing in a
        # generator (which is not true for namedtuples, handled
        # above).
        return type(obj)(serialize_dc(v, dict_factory) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)(
            (serialize_dc(k, dict_factory), serialize_dc(v, dict_factory))
            for k, v in obj.items()
        )
    else:
        return copy.deepcopy(obj)


def node_class(name):
    return getattr(__import__("libcst"), name)


def unserialize_dc(s, k=None):
    from libcst import MaybeSentinel

    if s == "MaybeSentinel.DEFAULT":
        return MaybeSentinel.DEFAULT
    if type(s) == list:
        s = [unserialize_dc(x) for x in s]
        if k in ["lpar", "rpar"]:
            s = tuple(s)
        return s
    if type(s) == tuple:
        return tuple([unserialize_dc(x) for x in list(s)])
    if type(s) != dict or not "type" in s:
        return s
    args = {
        "type" if k == "type_param" else k: unserialize_dc(v, k)
        for k, v in s.items()
        if k != "type"
    }
    klass = node_class(s["type"])
    try:
        return klass(**args)
    except Exception as e:
        print(klass)
        print(s)
        print(args)
        raise
