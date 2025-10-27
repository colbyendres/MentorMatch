import os 
import json
import numpy as np
import csv

from itertools import zip_longest
from models import Person
from scipy.optimize import linear_sum_assignment
from config import Config

class PeopleInfo:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.to_index = {} # Person name -> idx in mentors/mentees
        if not os.path.exists(self.file_path):
            raise FileNotFoundError()
        with open(self.file_path, 'rt') as fp:
            self.data = json.load(fp)
            self.mentors = self._init_group(self.data['mentors'], True)            
            self.mentees = self._init_group(self.data['mentees'], False)

    def _init_group(self, data, is_mentor):
        group = []
        for idx, name in enumerate(data):
            person = Person(name, data[name]['prefs'], is_mentor)
            group.append(person)
            self.to_index[name] = idx
        return group
    
    def construct_matrix(self):
        m,n = len(self.mentors), len(self.mentees)
        if m != n:
            # TODO: Handle case when mapping isn't a bijection
            raise ValueError('Number of mentees and mentors differ!')
        mat = np.zeros((m,n))
        for person in self.mentors:
            row_idx = self.to_index[person.name]
            for pref in person.prefs:
                mat[row_idx][self.to_index[pref]] += 1
        
        for person in self.mentees:
            col_idx = self.to_index[person.name]
            for pref in person.prefs:
                mat[self.to_index[pref]][col_idx] += 1      
    
        return mat
    
    def add_person(self, name, position, prefs):
        p = Person(name, prefs, position == 'mentor')
        if position == 'mentor':
            self.mentors.append(p)
        else:
            self.mentees.append(p)
        self._write_back(p)
        
    def _write_back(self, person):
        if person.is_mentor:
            self.data['mentors'][person.name] = {'prefs': person.prefs}
        else:
            self.data['mentees'][person.name] = {'prefs': person.prefs}
        with open(self.file_path, 'w') as fp:
            json.dump(self.data, fp, indent=4)
    
    def get_people(self):
        return zip_longest(self.mentors, self.mentees, fillvalue=None)
    
    def get_from_indices(self, row_idx, col_idx):
        mentor_names, mentee_names = [], []
        for row, col in zip(row_idx, col_idx):
            mentor_names.append(self.mentors[row].name)
            mentee_names.append(self.mentees[col].name)
        return mentor_names, mentee_names
    
class Matcher:
    def __init__(self, p_info: PeopleInfo):
        self.people_info = p_info
        self.matches = []
        
    def match(self):
        mat = self.people_info.construct_matrix()
        row_idx, col_idx = linear_sum_assignment(-mat)
        mentor_names, mentee_names = self.people_info.get_from_indices(row_idx, col_idx)
        scores = [mat[row_idx[i]][col_idx[i]] for i in range(len(row_idx))]
        self.matches = list(zip(mentor_names, mentee_names, scores))
        return self.matches
    
    def get_cached_matches(self):
        return self.matches
    
    def download_match(self):
        with open(Config.REMOTE_MATCH_FILE, 'w', newline='') as fp:
            writer = csv.writer(fp)
            # Headers
            writer.writerow(['Mentor', 'Mentee', 'Matching Score'])
            writer.writerows(self.matches)