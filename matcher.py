import os
import json
import numpy as np
import csv

from models import Person, Preference
from config import Config

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from itertools import zip_longest
from scipy.optimize import linear_sum_assignment


class PeopleInfo:

    ROW = 0
    COL = 1
    
    def __init__(self, session):
        self.db = session
        self.matrix_index = {} # db index -> row/col in pref matrix
        self.mentors = []
        self.mentees = []
        self.mentor_prefs = None # preferences of mentors[i]
        self.mentee_prefs = None # preferences of mentees[i]
        self.match_invalidated = False
        
    def _cache_people(self):
        if self.mentors and self.mentees:
            return
        all_people = self.db.query(Person).all()
        curr_row, curr_col = 0, 0
        for person in all_people:
            if person.is_mentor:
                self.mentors.append(person.name)
                self.matrix_index[person.id] = (PeopleInfo.ROW, curr_row)
                curr_row += 1
            else:
                self.mentees.append(person.name)
                self.matrix_index[person.id] = (PeopleInfo.COL, curr_col)
                curr_col += 1
                
    def _cache_prefs(self):
        if self.mentee_prefs and self.mentor_prefs:
            return
        # Populate the mentor/mentee arrays from people table
        # The prefs arrays should be parallel to the original arrays
        self._cache_people()
        self.mentee_prefs = [[] for _ in range(len(self.mentees))]
        self.mentor_prefs = [[] for _ in range(len(self.mentors))]
        
        prefs = self.db.query(Preference).all()
        for pref in prefs:
            # Get the index and row/column axis for both people
            p1_axis, p1_idx = self.matrix_index[pref.preferrer_id]
            p2_axis, p2_idx = self.matrix_index[pref.preferee_id]
            
            # Relationship between members of same status, integrity error
            if p1_axis == p2_axis:
                raise ValueError()
            
            if p1_axis == PeopleInfo.ROW: # is a mentor
                self.mentor_prefs[p1_idx].append(self.mentees[p2_idx])
            else: # is a mentee
                self.mentee_prefs[p1_idx].append(self.mentors[p2_idx])
            

    def construct_matrix(self):
        self._cache_people()
        num_mentors = len(self.mentors)
        num_mentees = len(self.mentors)
        if num_mentors != num_mentees:
            # TODO: Handle case when mapping isn't a bijection
            raise ValueError('Number of mentees and mentors differ!')

        mat = np.zeros((num_mentors, num_mentees))
        prefs = self.db.query(Preference).all()
        for pref in prefs:
            # Get the index and row/column axis for both people
            p1_axis, p1_idx = self.matrix_index[pref.preferrer_id]
            p2_axis, p2_idx = self.matrix_index[pref.preferee_id]
            
            # Relationship between members of same status, integrity error
            if p1_axis == p2_axis:
                raise IntegrityError('Relationship between members of the same status')

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
        # Get IDs from preferred partners' names
        pref_db_ids = self.db.query(Person.id).filter(Person.name.in_(prefs)).all()
        prefs = [Preference(preferrer_id=p.id, preferee_id=id) for id in pref_db_ids]
        
        # Write to DB
        try:
            self.db.add(p)
            self.db.add_all(prefs)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        
        # Update cached mentor/mentee information
        if is_mentor:
            self.mentors.append(name)
            self.matrix_index[p.id] = (PeopleInfo.ROW, len(self.mentors)-1)
        else:
            self.mentees.append(name)
            self.matrix_index[p.id] = (PeopleInfo.COL, len(self.mentees)-1)
            
        self.match_invalidated = True
        
    def delete_person(self, name, position):
        # NOTE: Assume that (name, position) pairs are unique
        # This is a tenuous assumption and will probably need to be revisited
        is_mentor = position.lower() == 'mentor'
        try:
            person = self.db.query(Person).filter(Person.name == name, Person.is_mentor == is_mentor).one()
            self.db.delete(person)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        
        # Invalidate all data and force a re-cache
        # NOTE: We cannot simply remove the person from the arrays/index
        # This breaks the sequential nature of the values (i.e. the row/col indices)
        self.mentors = []
        self.mentees = []
        self.matrix_index = {}
        self.mentor_prefs = None
        self.mentee_prefs = None
        self.match_invalidated = True

    def get_people_with_prefs(self):
        self._cache_prefs()
        mentees_as_str = [', '.join(pref) for pref in self.mentee_prefs]
        mentors_as_str = [', '.join(pref) for pref in self.mentor_prefs]
        return zip_longest(self.mentors, self.mentees, mentors_as_str, mentees_as_str, fillvalue=None)

    def get_from_indices(self, mentor_idx, mentee_idx):
        """
        Get names of mentors and mentees from matrix indices
        
        Args:
            mentor_idx (list[int]): subset of row indices in preference matrix
            mentee_idx (list[int]): subset of column indices in preference matrix
            
        Returns:
            mentor_names, mentee_names (list[str], list[str]): names of people
        """
        self._cache_people()
        return [self.mentors[i] for i in mentor_idx], [self.mentees[i] for i in mentee_idx]

    def get_from_name(self, user_name, is_mentor=False):
        return self.db.query(Person).filter(Person.name == user_name, Person.is_mentor == is_mentor).one()

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
