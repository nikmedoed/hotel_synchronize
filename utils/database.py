import elara
from collections import defaultdict

BNOVO_TAG = "bnovoID"
WUBOOK_TAG = 'wubookID'

# база хранит ключ в формате метка_системы:id_системы = id_другой системы
synchrobase = elara.exe("elara.db", commitdb=True)


def key(pref, i):
    return f"{pref}:{i}"


class Feedback:
    cache = defaultdict(set)

    def add(self, key, wubookId):
        self.cache[wubookId].add(key)

    def delete(self, wubookId):
        temp = self.cache.pop(wubookId, None)
        if temp:
            for kk in temp:
                synchrobase.rem(kk)
        else:
            for kk in synchrobase.getkeys():
                if synchrobase[kk] == wubookId and kk.startswith(BNOVO_TAG):
                    synchrobase.rem(kk)


wubook_multiroom_feedback = Feedback()
