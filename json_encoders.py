from solution import Solution


def my_json_encoder(obj):
    if isinstance(obj, Solution):
        res = obj.__dict__
        res.update({'__type': 'Solution'})
        return res
    raise TypeError("Unknown type in my_json_encoder")


def my_json_decoder(dct):
    if '__type' not in dct:
        return dct
    if dct['__type'] == 'Solution':
        res = Solution()
        res.by_dict(dct)
        return res
    raise TypeError("Unknown type in my_json_decoder")
