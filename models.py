import logging


class Person:
    def __init__(self, name, prefs, is_mentor):
        self.name = name
        self.prefs = prefs
        self.is_mentor = is_mentor

    def get_prefs_pretty(self):
        return ', '.join(self.prefs)

    def __str__(self):
        return f'{self.name} prefers: [{self.prefs}]'

    def __repr__(self):
        return self.name

    def __hash__(self):
        # TODO: This breaks if two mentors/mentees share a name
        return hash((self.name, self.is_mentor))
