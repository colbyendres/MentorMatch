from app.models import Person, Preference
from app.matcher import PeopleInfo

def add_people_with_prefs(session, people, prefs):
    people_ids = {}
    for spec in people:
        p = Person(**spec)
        session.add(p)
        session.flush()
        people_ids[p.name] = p.id
    
    for preferrer, preferee in prefs:
        pref = Preference(preferrer_id=people_ids[preferrer], preferee_id=people_ids[preferee])
        session.add(pref)
    
    session.commit()
    p_info = PeopleInfo(session)
    return p_info


