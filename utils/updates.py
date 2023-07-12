from utils.database import synchrobase, key


def split_dict(bookings, tag):
    # Удалит из списка брони, что были в базе, вернёт список удалённого
    result = {}
    for book_key in set(bookings.keys()):
        if synchrobase.get(key(tag, book_key)):
            result[book_key] = bookings[book_key]
            del bookings[book_key]
    return result


def make_updates(bookings, bookins_original, tag, function, rooms_copy_to_origin):
    for book_id, book in bookings.items():
        orig_id = synchrobase.get(key(tag, book_id))
        orig = bookins_original.pop(orig_id, None)
        if not orig:
            continue
        function(book, orig, rooms_copy_to_origin)
