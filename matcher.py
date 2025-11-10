import numpy as np
import csv

from models import Person, Preference
from config import Config

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from itertools import zip_longest
from scipy.optimize import linear_sum_assignment

class PeopleInfo:

    ROW = 0
    COL = 1

    def __init__(self, session):
        self.db = session
        self.matrix_index = {}  # db index -> row/col in pref matrix
        self.db_index = {}  # row/col in pref matrix -> db index
        self.num_mentors = 0
        self.num_mentees = 0
        self.match_invalidated = True

    def _map_to_matrix(self):
        """
        Map DB id to corresponding row/column in preference matrix

        Args:
            None
        Returns:
            matrix_index (dict): db id to matrix row/col number pairing
        """
        all_people = self.db.query(Person).all()
        self.num_mentors, self.num_mentees = 0,0
        for person in all_people:
            if person.is_mentor:
                self.matrix_index[person.id] = (
                    PeopleInfo.ROW, self.num_mentors)
                self.db_index[(PeopleInfo.ROW, self.num_mentors)] = person.id
                self.num_mentors += 1
            else:
                self.matrix_index[person.id] = (
                    PeopleInfo.COL, self.num_mentees)
                self.db_index[(PeopleInfo.COL, self.num_mentees)] = person.id
                self.num_mentees += 1

    def construct_matrix(self):
        if not self.matrix_index or not self.db_index:
            self._map_to_matrix()
        if self.num_mentors != self.num_mentees:
            # TODO: Handle case when mapping isn't a bijection
            raise ValueError('Number of mentees and mentors differ!')

        mat = np.zeros((self.num_mentors, self.num_mentees))
        prefs = self.db.query(Preference).all()
        for pref in prefs:
            # Get the index and row/column axis for both people
            p1_axis, p1_idx = self.matrix_index[pref.preferrer_id]
            p2_axis, p2_idx = self.matrix_index[pref.preferee_id]

            # Relationship between members of same status, integrity error
            if p1_axis == p2_axis:
                raise ValueError(
                    'Relationship between members of the same status')

            if p1_axis == PeopleInfo.ROW:
                # P1 is a mentor, so P2 must be a mentee
                mat[p1_idx][p2_idx] += 1
            else:
                # P1 is a mentee, so P2 must be a mentor
                mat[p2_idx][p1_idx] += 1
                
        self.match_invalidated = False
        return mat

    def add_person(self, name: str, position: str, prefs: list[str], email=None):
        is_mentor = position.lower() == 'mentor'
        p = Person(name=name, is_mentor=is_mentor, email=email)
        try:
            # We must flush the write to the people table first
            # Otherwise, p won't be assigned an ID
            self.db.add(p)
            self.db.flush()

            # Get IDs from preferred partners' names
            pref_db_ids = self.db.query(Person.id).filter(
                Person.name.in_(prefs)).all()
            prefs = [Preference(preferrer_id=p.id, preferee_id=id[0])
                     for id in pref_db_ids]

            # Write preferences
            self.db.add_all(prefs)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # Update cached mentor/mentee information
        if is_mentor:
            self.matrix_index[p.id] = (PeopleInfo.ROW, self.num_mentors)
            self.db_index[(PeopleInfo.ROW, self.num_mentors)] = p.id
            self.num_mentors += 1
        else:
            self.matrix_index[p.id] = (PeopleInfo.COL, self.num_mentees)
            self.db_index[(PeopleInfo.COL, self.num_mentees)] = p.id
            self.num_mentees += 1
            
        self.match_invalidated = True

    def delete_person(self, name):
        try:
            person = Person.query.filter_by(name=name).first()
            if not person:
                raise ValueError(f'Person {name} not found')
            self.db.delete(person)
            self.db.commit()
        except ValueError as e:
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

        # Invalidate mapping data
        # NOTE: We cannot simply remove the person from the dictionary
        # This breaks the sequential nature of the values (i.e. the row/col indices)
        # NOTE: We could be more selective, keeping people who's status differs from the deleted person
        self.matrix_index = {}
        self.db_index = {}
        self.match_invalidated = True

    def edit_person(self, old_name, new_name, new_is_mentor, new_prefs):
        try:
            p = self.get_from_name(old_name)
            p.name = new_name
            p.is_mentor = new_is_mentor

            # Delete all outgoing preferences for p
            # We don't need to touch incoming preferences, since p's id is unchanged on edit
            Preference.query.filter_by(preferrer_id=p.id).delete()

            # Write new preferences
            pref_db_ids = self.db.query(Person.id).filter(
                Person.name.in_(new_prefs)).all()
            prefs = [Preference(preferrer_id=p.id, preferee_id=id[0])
                     for id in pref_db_ids]
            self.db.add_all(prefs)
            self.db.commit()
        except ValueError as e:
            # Thrown by get_from_name, no need to rollback
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
        
        self.match_invalidated = True

    def get_people_without_prefs(self):
        mentors, mentees = [], []
        for person in Person.query.all():
            if person.is_mentor:
                mentors.append(person)
            else:
                mentees.append(person)
        return mentors, mentees
    
    def get_people_with_prefs(self):
        mentors, mentees = [], []
        mentor_prefs, mentee_prefs = [], []
        for person in Person.query.all():
            if person.is_mentor:
                mentors.append(person)
                mentor_prefs.append(person.get_prefs_as_str())
            else:
                mentees.append(person)
                mentee_prefs.append(person.get_prefs_as_str())
        return list(zip_longest(mentors, mentees, mentor_prefs, mentee_prefs, fillvalue=None))
    
    def get_from_indices(self, mentor_idx, mentee_idx):
        """
        Get names of mentors and mentees from matrix indices

        Args:
            mentor_idx (list[int]): subset of row indices in preference matrix
            mentee_idx (list[int]): subset of column indices in preference matrix

        Returns:
            mentor_names, mentee_names (list[str], list[str]): names of people
        """
        assert len(mentor_idx) == len(mentee_idx)
        db_ids = [self.db_index[(PeopleInfo.ROW, idx)] for idx in mentor_idx]
        db_ids.extend([self.db_index[(PeopleInfo.COL, idx)] for idx in mentee_idx])
        people = self.db.query(Person.name).filter(Person.id.in_(db_ids)).order_by(
            func.array_position(db_ids, Person.id)).all()
        people = [p for (p,) in people]
        n = len(people) // 2
        return people[:n], people[n:]

    def get_from_name(self, user_name):
        p = Person.query.filter_by(name=user_name).first()
        if not p:
            raise ValueError(f'Person {user_name} not found')
        return p


class Matcher:
    def __init__(self, p_info: PeopleInfo):
        self.people_info = p_info
        self.matches = []

    def match(self):
        mat = self.people_info.construct_matrix()
        row_idx, col_idx = linear_sum_assignment(
            cost_matrix=mat, maximize=True)
        mentor_names, mentee_names = self.people_info.get_from_indices(
            row_idx, col_idx)
        scores = [mat[row_idx[i]][col_idx[i]] for i in range(len(row_idx))]
        self.matches = list(zip(mentor_names, mentee_names, scores))
        return self.matches

    def _ensure_valid_match(self):
        if self.people_info.match_invalidated:
            self.match()

    def get_cached_matches(self):
        self._ensure_valid_match()
        return self.matches

    def download_match(self):
        self._ensure_valid_match()
        with open(Config.REMOTE_MATCH_FILE, 'w', newline='') as fp:
            writer = csv.writer(fp)
            # Headers
            writer.writerow(['Mentor', 'Mentee', 'Matching Score'])
            writer.writerows(self.matches)
