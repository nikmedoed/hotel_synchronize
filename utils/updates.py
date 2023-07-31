from utils.database import synchrobase, key


def split_dict(bookings, tag):
    # Удалит из списка брони, что были в базе, вернёт список дубликатов из другой системы
    originals = {}
    for book_key in set(bookings.keys()):
        if synchrobase.exists(key(tag, book_key)):
            originals[book_key] = bookings.pop(book_key)
    return originals


def make_updates(bookings, bookins_original: dict, tag, function, rooms_copy_to_origin):
    # Эта фукнция обновляет копии броней и убирает "проверенные" из словарей.
    # Из-за необходимости обрабатывать несколько номеров в одной брони из вубука,
    # удаляем записи отдельным циклом после обработки.
    # Это позволяет обойти и другую проблему: после удаления связки ключей,
    # синхронизатор в ближайшую итерацию или сразу создаст копии для оставшихся номеров в вубуке
    todel = set()
    for book_id, book in bookings.items():
        orig_id = synchrobase.get(key(tag, book_id))
        orig = bookins_original.get(orig_id, None)
        if not orig:
            continue
        todel.add(orig_id)
        function(book, orig, rooms_copy_to_origin)
    for i in todel:
        del bookins_original[i]

