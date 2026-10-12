from werkzeug.exceptions import BadRequest


def parse_cursor(value):
    if value is None:
        return None

    try:
        cursor = int(value)
    except (TypeError, ValueError) as exc:
        raise BadRequest("Curseur de pagination invalide.") from exc

    if cursor <= 0:
        raise BadRequest("Curseur de pagination invalide.")
    return cursor
