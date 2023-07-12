import elara

BNOVO_TAG = "bnovoID"
WUBOOK_TAG = 'wubookID'

# база хранит ключ в формате метка_системы:id_системы = id_другой системы
synchrobase = elara.exe("elara.db", commitdb=True)


def key(pref, i):
    return f"{pref}:{i}"
