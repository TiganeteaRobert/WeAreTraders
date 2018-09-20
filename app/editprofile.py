import json
import requests
from flask import current_app


def editprofile(username, about_me):
    r = requests.get(username, about_me,
                     headers=newuserdata)
    if r.status_code != 200:
        return _('Error')
    return json.loads(r.content.decode('utf-8-sig'))
