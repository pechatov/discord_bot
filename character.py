import time


class Character:
    def __init__(self, name=None, url=None, rio=0, region=None, realm=None,
                 neck_level=0, item_level=0, corruption=dict(),
                 c=None, spec=None, faction=None):
        self.name = name
        self.url = url
        self.rio = rio
        self.c = c
        self.spec = spec
        self.region = region
        self.realm = realm
        self.faction = faction
        if faction == 'horde':
            self.faction_logo_url = 'https://cdnassets.raider.io/images/site/horde_logo_xs.png'
        else:
            self.faction_logo_url = 'https://cdnassets.raider.io/images/site/alliance_logo_xs.png'
        self.spec_logo = 'https://cdnassets.raider.io/images/classes/spec_' + c + '_' + spec + '.png'
        self.neck_level = neck_level
        self.item_level = item_level
        self.corruption_total = corruption['added']
        self.corruption_resistance = corruption['resisted']
        self.corruptions = ['_'.join(corrupt['name'].lower().split()) for corrupt in corruption['spells']]
        self._timestamp = time.time()
        self.links = dict()
        self.level = dict()

    def __repr__(self):
        result = ''
        for field in character.__dir__():
            value = character.__getattribute__(field)
            if isinstance(value, str) or isinstance(value, int):
                result += '{}: {}\n'.format(field, value)
        return result
