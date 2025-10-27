from . import db
from flask_login import UserMixin

# This is the model for what variables will be in an entry in the database. If you change the variables, you will probably need to make a new database or delete everything within the current database or else the website will freak out
class Scout(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)

  # Match Info
  regional = db.Column(db.String(20))
  round = db.Column(db.String(20))
  alliance = db.Column(db.String(20))
  team = db.Column(db.String(20))

  # Autonomous Info  
  starting_pos = db.Column(db.String(20))
  auton_amp = db.Column(db.String(20))
  auton_speaker = db.Column(db.String(20))
  auton_notes = db.Column(db.String(20))
  auton_community = db.Column(db.String(20))

  # Tele-op Info
  tele_amp = db.Column(db.String(20))
  tele_amped_amp = db.Column(db.String(20))
  tele_speaker = db.Column(db.String(20))
  tele_trap = db.Column(db.String(20))
  times_amplified = db.Column(db.String(20))
  tele_notes = db.Column(db.String(20))
  coopertition = db.Column(db.String(20))

  # Endgame Info
  stage = db.Column(db.String(20))
  harmony = db.Column(db.String(20))
  spotlight = db.Column(db.String(20))

  # Other stuff
  role = db.Column(db.String(20))
  win = db.Column(db.String(20))

  # Notes
  notes = db.Column(db.String(200))
