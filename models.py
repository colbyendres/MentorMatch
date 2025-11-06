from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Person(db.Model):
    __tablename__ = 'people'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    is_mentor = db.Column(db.Boolean, nullable=False)
    email = db.Column(db.String, nullable=True)
    
    given_prefs = db.relationship(
        "Preference",
        foreign_keys="Preference.preferrer_id",
        back_populates="preferrer",
        cascade="all, delete-orphan"
    )

    received_prefs = db.relationship(
        "Preference",
        foreign_keys="Preference.preferee_id",
        back_populates="preferee",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return self.name
    
    def get_prefs_as_str(self):
        return ', '.join([p.preferee.name for p in self.given_prefs])

class Preference(db.Model):
    __tablename__ = 'prefs'

    id = db.Column(db.Integer, primary_key=True)
    preferrer_id = db.Column(
        db.Integer, db.ForeignKey('people.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    preferee_id = db.Column(
        db.Integer, db.ForeignKey('people.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )

    preferrer = db.relationship(
        "Person",
        foreign_keys=[preferrer_id],
        back_populates="given_prefs"
    )
    preferee = db.relationship(
        "Person",
        foreign_keys=[preferee_id],
        back_populates="received_prefs"
    )

    def __repr__(self):
        return f'Person {self.preferrer_id} prefers {self.preferee_id}'
