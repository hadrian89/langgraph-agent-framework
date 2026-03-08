import uuid


def get_or_create_session(session_id):

    if not session_id:
        session_id = str(uuid.uuid4())

    return session_id
