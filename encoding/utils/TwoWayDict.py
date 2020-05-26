class TwoWayDict(dict):
    def __len__(self):
        return int(dict.__len__(self) / 2)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __init__(self, mapping):

        for key in mapping:
            dict.__setitem__(self, key, mapping[key])
            dict.__setitem__(self, mapping[key], key)

