from email.mime import image
from flask import Blueprint, render_template, request, flash, redirect, session, url_for, Response
from .models import Scout
from . import db
import csv
import os
import shutil
from io import BytesIO
import base64
import tbapy
import requests
import qrcode
import qrcode.image.svg
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import cast, Integer

from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D


# Welcome future scouting website programmers! This is the page where most of the code and functionality is written. If you need help contact me (Tyler Tang '24) at osl6577z@gmail.com

#tba = tbapy.TBA(
# 'h39XHSEqXkc59WvXY0lteYagmwOzWD0wmLV2CxZulOMcB89YIHFUIczJxvGTtM6X')

# This is the TBA API key. You can get one from the TheBlueAlliance website. I made this using my own account, so you'll probably need to get one if my account expires or something. https://www.thebluealliance.com/
tba_key = 'w9Rg74721yfHACYNd4iGm9BCrJ9lZyyGERyCFjdRau0u17TPapeNRJyMLlliCRuB'
tba = tbapy.TBA(tba_key)

# This is the event key for the event we are pulling team numbers from. You can get the event key by searching it up on the TBA website or the firstinspires.org website. 
# DO NOT FORGET TO CHANGE THE EVENT KEY FOR EVERY REGIONAL!!!!!
event_key = '2024ausc'

api_url = 'https://www.thebluealliance.com/api/v3/event/' + event_key + '/teams/simple'
headers = {'X-TBA-Auth-Key': tba_key}
response = requests.get(api_url, headers=headers)

# Get team numbers from TBA APi to display on the website for the team dropdown menu
all_teams = []
if response.status_code == 200:
  # Parse the JSON response
  teams = response.json()

  # Extract team numbers and nicknames
  team_numbers = [team['team_number'] for team in teams]
  team_numbers.insert(0, "")
  team_nicknames = [team['nickname'] for team in teams]
  team_nicknames.insert(0, "")

  min_length = min(len(team_numbers), len(team_nicknames))
  all_teams = [(team_numbers[i], team_nicknames[i]) for i in range(min_length)]

  
""" No idea what this is, I didn't write this
#round = "2023bcvi_qm" + Scout.round
#print(round)
#all_teams_simple = tba.event_teams(round, "simple")
all_teams_simple = tba.event_teams(event_key, "simple")
all_teams = []
for i in range(len(all_teams_simple)):
  all_teams.append(all_teams_simple[i]['team_number'])
"""

# idk but this is very important
auth = Blueprint('auth', __name__)


# This is supposed to make a qr code to the scouting website, but I just made one using some random qr code website to use instead, which I placed in the static folder. The image generated is not used in the code yet
img = qrcode.make('https://frc-raidzero-2023-scout-website.24tylert.repl.co',
                  image_factory=qrcode.image.svg.SvgImage)
with open('website/static/qr.svg', 'wb') as qr:
  img.save(qr)

  
# Setup for Google Sheets editing
scope = [
  'https://spreadsheets.google.com/feeds',
  'https://www.googleapis.com/auth/drive'
]
# I created a robot service account that can access google sheets to pull data and edit it. Search up how to use google service accounts to make your own and replace the current credentials.json file with your own.
sheet = None
try:
  credentials = Credentials.from_service_account_file('credentials.json',
                                                      scopes=scope)
  client = gspread.authorize(credentials)
  document = client.open_by_url("https://docs.google.com/spreadsheets/d/1VrrXeGQ2-DlEfD2Epyr-opKc31NNFea5VHrrIsdgrzM/edit#gid=169386782")
  sheet = document.sheet1
except Exception as e:
  print(f"Google Sheets unavailable: {e}")

# Password for the "delete all data" button from the data page
# Clark was our strategist and head scout lmao
# Keep the password the same to honor The Great Clark's legacy
secret_password = "all hail clark"




# Input a single string of data split by @ signs, updates the google sheets with the data split into different columns, then returns the data in an array format
def update_google_sheet(data):
  # Turns single line of data into array, using @ signs as symbol to split
  split_data = data.split('@')
  if (split_data[0]!="placeholder data"):
    split_data[0] = int(split_data[0])

  for piece in split_data:
    # Check for duplicates
    values_list = sheet.get_all_values()
    is_duplicate = False

    for row in values_list:
      if piece in row:
        is_duplicate = True
        break

    if not is_duplicate:
      # Adds data to google sheets
      sheet.append_row(split_data)

  return split_data


# Updates csv based off of the SQLalchemy database, so that the dataframe can be updated... yes theres 3 copies of all the data... but it works so whatever
def write_to_csv():
  data = Scout.query.all()
  print(len(data))
  #data = sorted(data, key=calculate_total_points, reverse=True)
  # Define the file path for the CSV file
  csv_file_path = 'website/static/data.csv'

  # Write the filtered data to a CSV file
  with open(csv_file_path, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # Write header row
    csv_writer.writerow([
      "Team", "Round", "Alliance","Starting_pos",
      "Auton_amp", "Auton_speaker", "Auton_notes","Auton_community",
      "Tele_amp", "Tele_speaker", "Tele_trap", "Times_amplified", "Tele_notes",
      "Coopertition", "Stage", "Spotlight", "Harmony",
       "Role", "Notes"
    ])


    # Write data rows
    for row in data:
      csv_writer.writerow([
        row.team, row.round, row.alliance, row.starting_pos,
        row.auton_amp, row.auton_speaker, row.auton_notes, row.auton_community,
        row.tele_amp, row.tele_speaker, row.tele_trap, row.times_amplified, row.tele_notes,
        row.coopertition, row.stage, row.spotlight, row.harmony,
         row.role, row.notes
      ])





# Sets up creation and usage of radar graphs
# Don't mess with this I just copy pasted it so I don't understand it at all
def radar_factory(num_vars, frame="circle"):
  theta = np.linspace(0, 2*np.pi, num_vars, endpoint=False)


  class RadarTransform(PolarAxes.PolarTransform):

    def transform_path_non_affine(self, path):
        # Paths with non-unit interpolation steps correspond to gridlines,
        # in which case we force interpolation (to defeat PolarTransform's
        # autoconversion to circular arcs).
        if path._interpolation_steps > 1:
            path = path.interpolated(num_vars)
        return Path(self.transform(path.vertices), path.codes)
  
  class RadarAxes(PolarAxes):
    name = 'radar'
    PolarTransform = RadarTransform
  
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # rotate plot such that the first axis is at the top
        self.set_theta_zero_location('N')
  
    def fill(self, *args, closed=True, **kwargs):
        """Override fill so that line is closed by default"""
        return super().fill(closed=closed, *args, **kwargs)
  
    def plot(self, *args, **kwargs):
        """Override plot so that line is closed by default"""
        lines = super().plot(*args, **kwargs)
        for line in lines:
            self._close_line(line)
  
    def _close_line(self, line):
        x, y = line.get_data()
        # FIXME: markers at x[0], y[0] get doubled-up
        if x[0] != x[-1]:
            x = np.append(x, x[0])
            y = np.append(y, y[0])
            line.set_data(x, y)
  
    def set_variables(self, labels):
        self.set_thetagrids(np.degrees(theta), labels)
  
    def _gen_axes_patch(self):
        # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
        # in axes coordinates.
        if frame == 'circle':
            return Circle((0.5, 0.5), 0.5)
        elif frame == 'polygon':
            return RegularPolygon((0.5, 0.5), num_vars,
                                  radius=.5, edgecolor="k")
        else:
            raise ValueError("Unknown value for 'frame': %s" % frame)
  
    def _gen_axes_spines(self):
        if frame == 'circle':
            return super()._gen_axes_spines()
        elif frame == 'polygon':
            # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
            spine = Spine(axes=self,
                          spine_type='circle',
                          path=Path.unit_regular_polygon(num_vars))
            # unit_regular_polygon gives a polygon of radius 1 centered at
            # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
            # 0.5) in axes coordinates.
            spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                                + self.transAxes)
            return {'polar': spine}
        else:
            raise ValueError("Unknown value for 'frame': %s" % frame)
  register_projection(RadarAxes)
  return theta





# Initialize DataFrame for graph creation
df = pd.read_csv('website/static/data.csv')


# These auth.route things renders the page. Enter variables you need to pass onto the html page in the 'return render_template()' line. Ex. return render_template('index.html', name=name) to use variable 'name' in the index html page.
# All of the html pages currently in use extend base.html. This is because the base.html defines all the formatting things and sets up harder html shenangans that I honestly do not understand
@auth.route('/')
@auth.route('/home')
def home():
  return render_template('home.html')


# Hmtl page not in use anymore. for a scrapped idea
"""
@auth.route('/qrcode')
def generateqr():
  return render_template('qrcode.html')
"""




# DATA ----------------------------------------------
# Data html page
@auth.route('/data', methods=['GET', 'POST'])
def data():
  # Show all the scouting data
  #data = Scout.query.order_by(Scout.team).all()
  #data =  Scout.query.filter(Scout.round.in_(['05', '64034'])).all()
  data = Scout.query.all()
  print(len(data))
  did_sort = False
  graph_made = False
  sort_by_specific_team = False
  team_sort_number = 0
  searched_team = ""

  # Updates csv before updating dataframe, which is based off of data.csv
  write_to_csv()
  df = pd.read_csv('website/static/data.csv')

  
  

  # If the user pressed the ^ or v buttons in the data page, it will append ?sort_by=[insert argument here] to the url. This line checks for which variable to sort by
  sort_by = request.args.get('sort_by')

  # add to this list to add more sort options
  if sort_by == 'team':
    sorted_data = Scout.query.order_by(cast(Scout.team, Integer)).all()
  elif sort_by == 'teamreverse':
    sorted_data = Scout.query.order_by(cast(Scout.team, Integer).desc()).all()
  elif sort_by == 'round':
    sorted_data = Scout.query.order_by(cast(Scout.round, Integer)).all()
  elif sort_by == 'roundreverse':
    sorted_data = Scout.query.order_by(cast(Scout.round, Integer).desc()).all()
  # Adds functionality to the links for the team numbers in the table
  elif sort_by != None:
    sorted_data = Scout.query.all()
    team_sort_number = sort_by
    sort_by_specific_team = True
  else:
    sorted_data = data

  
  # Search teams and delete all data buttons
  # Both buttons are part of the same form so you need to check which button is pressed, otherwise the functions of both buttons will happen when either is pressed
  # The sort_by_specific_team is used to check which teams number was clicked in the data table separate from the search bar
  if request.method == 'POST' or sort_by_specific_team:
    action = ""
    
    if request.method == 'POST':
      action = request.form.get('action')
      searched_team = request.form.get('searched_team')
    else:
      searched_team = team_sort_number
    if (action == "Search Team" or sort_by_specific_team and searched_team != ""):
      did_sort = True
      sorted_data = Scout.query.filter_by(team=searched_team).all()
      team_entries = []
      team_entries_averaged = []
      
      # Creating arrays and matrices to plot onto graph
      for x in df.index:
        if df.loc[x, 'Team'] != int(searched_team):
          df.drop(x, inplace = True)
      for x in df.index:
        print(df.loc[x, 'Team'])
        team_entries.append([df.loc[x, 'Auton_amp'], df.loc[x, 'Auton_speaker'], df.loc[x, 'Tele_amp'], df.loc[x, 'Tele_speaker'], df.loc[x, 'Times_amplified']])
        
    
      spoke_labels = ["Auton_amp", "Auton_speaker", "Tele_amp", "Tele_speaker", "Times_amplified"]
      print(team_entries)
      theta = radar_factory(len(team_entries[0]), frame="polygon")

      
      fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(projection='radar'))
      for d in team_entries:
          ax.plot(theta, d, color='b')
          ax.fill(theta, d, facecolor='b', alpha=0.25, label='_nolegend_')
      ax.set_variables(spoke_labels)

      labels = ("Auton_amp", "Auton_speaker", "Auton_notes")
      legend = ax.legend(labels, loc=(0.9, .95), labelspacing=0.1, fontsize='small')


      
      # Saves graph as png then atomically replaces the old graph with the new one
      fig.savefig('website/static/temp_team_averages.png')
      shutil.move('website/static/temp_team_averages.png', 'website/static/team_averages.png')
      graph_made = True
      
    # remember to db.session.commit() to save your changes!
    password = request.form.get('password')
    if (action == "Delete All" and password == secret_password):
      db.session.query(Scout).delete()
      db.session.commit()

  # Entries counting
  num_entries = len(sorted_data)
  
  # Converts dataframe database into html table
  html_table = df.to_html(index=False)

  return render_template('data.html', data=sorted_data, num_entries=num_entries, html_table=html_table, graph_made=graph_made, searched_team=searched_team)




# EDIT --------------------------------------------------
# When edit button is pressed, goes to another html page to edit the specific piece of data
@auth.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
  datum = Scout.query.get(id)
  
  # yes i typed everything in here manually. kill me now
  if request.method == 'POST':
    team = request.form.get('team')
    round = request.form.get('round')
    alliance = request.form.get('alliance')
    starting_pos = request.form.get('starting_pos')
    auton_amp = request.form.get('auton_amp')
    auton_speaker= request.form.get('auton_speaker')
    auton_notes= request.form.get('auton_notes')
    auton_community = request.form.get('auton_community')
    tele_amp = request.form.get('tele_amp')
    tele_speaker = request.form.get('tele_speaker')
    tele_trap = request.form.get('tele_trap')
    times_amplified = request.form.get('times_amplified')
    tele_notes = request.form.get('tele_notes')
    coopertition = request.form.get('coopertition')
    stage = request.form.get('stage')
    harmony = request.form.get('harmony')
    spotlight = request.form.get('spotlight')
    role = request.form.get('role')
    notes = request.form.get('notes')
    
    datum.team = team
    datum.round = round
    datum.alliance = alliance
    datum.starting_pos = starting_pos
    datum.auton_amp = auton_amp
    datum.auton_speaker = auton_speaker
    datum.auton_notes = auton_notes
    datum.auton_community = auton_community
    datum.tele_amp = tele_amp
    datum.tele_speaker = tele_speaker
    datum.tele_trap = tele_trap
    datum.times_amplified = times_amplified
    datum.tele_notes = tele_notes
    datum.coopertition = coopertition
    datum.stage = stage
    datum.harmony = harmony
    datum.spotlight = spotlight
    datum.stage = stage
    datum.role = role
    datum.notes = notes

    db.session.commit()
    
    return redirect('/data')
    #return render_template('data.html', id=id, data=data, num_entries=num_entries)
  return render_template('edit.html', id=id, datum=datum)





# Deletes data off of the database on the "Data" page. Not sure why it requires its own page, but if it works it works
@auth.route('/delete/<int:id>')
@auth.route('/delete', defaults={'id': None})
def delete(id):
  team_delete = Scout.query.get_or_404(id)
  db.session.delete(team_delete)
  db.session.commit()
  #data = Scout.query.order_by(Scout.team).all()
  return redirect('/data')
  #return render_template('data.html', data=data, num_entries=num_entries)





# DOWNLOAD -----------------------------------------

# Download the database
# Uses the csv where we wrote all the info down in order to display everything on the download page
@auth.route('/download', methods=['GET', 'POST'])
def download():
  #data = Scout.query.all()
  #retrieving problem, prints the same amount as above in data
  #data = Scout.query.filter(Scout.round.in_(['05', '64034'])).all()

  # variables for adding data to google sheets
  finished_adding = False
  report_new = 0;
  report_old = 0;
  
  write_to_csv()

  # Adds data to google sheets
  if request.method == "POST":
    values_list = sheet.get_all_values()
    data = Scout.query.all()

    data_to_add = []

    for datum in data:
      unique = True;
      team_match_info = [datum.team, datum.round, datum.alliance]
      print(team_match_info)
      for i in range(len(values_list)):
        prev_match_info = [values_list[i][0], values_list[i][1], values_list[i][2]]
        if team_match_info == prev_match_info:
          unique = False;
          report_old += 1
          break;

      if unique:
        report_new += 1
        datum_to_line = [int(datum.team), int(datum.round), datum.alliance, datum.starting_pos, int(datum.auton_amp), int(datum.auton_speaker), int(datum.auton_notes), int(datum.auton_community), int(datum.tele_amp), int(datum.tele_speaker), int(datum.tele_trap), int(datum.times_amplified), int(datum.tele_notes), int(datum.coopertition), int(datum.stage), int(datum.spotlight), int(datum.harmony), datum.role, datum.notes]
        data_to_add.append(datum_to_line)

    sheet.append_rows(data_to_add)
    finished_adding = True

  #return send_file(csv_file_path, as_attachment=True, attachment_filename='filtered_data.csv')
  return render_template('download.html',
                         attachment_filename='data.csv', finished_adding=finished_adding, report_new=report_new, report_old=report_old)






# SCOUTING -----------------------------------------------------------

# Scouting
# methods 'POST' happens when you submit the form.
@auth.route('/scout', methods=['GET', 'POST'])
def attempt():
  # need placeholder data to fill in qr code on first run, or else the qr code can't be generated and looks bad
  image_data = ""
  compressed_data = "placeholder data"

  # Pulls data from when you submit the information. Just a heads up, this runs before the rest of the code runs, in case you need to do some qr code shenanigans like with my placeholder data thing
  if request.method == 'POST':

    round = request.form.get('round')
    alliance = request.form.get('alliance')

    #TEAM 1
    team = request.form.get('team')

    # Auton
    starting_pos = request.form.get('starting_pos')

    auton_amp = request.form.get('auton_amp')
    auton_speaker = request.form.get('auton_speaker')
    auton_notes = request.form.get('auton_notes')
    auton_community = request.form.get('auton_community')

    # Teleop
    tele_amp = request.form.get('tele_amp')
    tele_speaker = request.form.get('tele_speaker')
    tele_trap = request.form.get('tele_trap')
    times_amplified = request.form.get('times_amplified')
    tele_notes = request.form.get('tele_notes')

    # EndGame
    coopertition = request.form.get('coopertition')
    stage = request.form.get('stage')
    harmony = request.form.get('harmony')
    spotlight = request.form.get('spotlight')

    # Other stuff
    role = request.form.get('role')
    #tier = request.form.get('tier')
    notes = request.form.get('notes')
    win = request.form.get('win')

    # Not sure what this does but is very important. Remember to update this when you want to add or delete variables
    new_scout = Scout(
      round=round,
      alliance=alliance,

      #Team 1
      team=team,
      starting_pos=starting_pos,
      auton_amp = auton_amp,
      auton_speaker = auton_speaker,
      auton_notes = auton_notes,
      auton_community=auton_community,
      tele_amp=tele_amp,
      tele_speaker=tele_speaker,
      tele_trap=tele_trap,
      times_amplified=times_amplified,
      tele_notes=tele_notes,
      coopertition = coopertition,
      stage = stage,
      harmony = harmony,
      spotlight =spotlight,
      role = role,
      #tier = tier,
      notes=notes,
      win=win)

    # No idea what this does either, but equally important
    try:
      db.session.add(new_scout)
      Scout.query.all()
      #Scout.query.filter(Scout.round.in_(['05', '64034', '30'])).all()
    except:
      db.session.rollback()
    else:
      try:
        db.session.commit()
      except:
        db.session.rollback()
        db.session.commit()

    # Store data as csv
    with open('website/static/data.csv', 'w') as s_key:
      csv_out = csv.writer(s_key)

      # Horizontal labels
      csv_out.writerow([
        "Team", "Round", "Alliance","Starting_pos",
        "Auton_amp", "Auton_speaker", "Auton_notes", "Auton_community",
        "Tele_amp", "Tele_speaker","Tele_trap", "Times_amplified",  "Tele_notes",
         "Coopertition", "Stage", "Harmony",
        "Spotlight", "Role", "Notes"
      ])

      # Database data
      data = db.session.query(
        Scout.team, Scout.round, Scout.alliance,
        Scout.starting_pos, Scout.auton_amp, Scout.auton_speaker, Scout.auton_notes,
        Scout.auton_community, Scout.tele_amp, Scout.tele_speaker, 
        Scout.tele_trap, Scout.times_amplified, Scout.tele_notes, Scout.coopertition, 
        Scout.stage, Scout.harmony, Scout.spotlight,
        Scout.role, Scout.notes)

      #Scout.tele_link, Scout.num_bot, Scout.win, Scout.rank_pt,

      for i in data:
        csv_out.writerow(i)

    # Convert data into single string for convenience and for qr code generation
    compressed_data = ''
    compressed_data += str(round) + "@"
    compressed_data += alliance + "@"
    compressed_data += str(team) + "@"
    compressed_data += starting_pos + "@"
    compressed_data += str(auton_amp) + "@"
    compressed_data += str(auton_speaker) + "@"
    compressed_data += str(auton_notes) + "@"
    compressed_data += str(auton_community) + "@"
    compressed_data += str(tele_amp) + "@"
    compressed_data += str(tele_speaker) + "@"
    compressed_data += str(tele_trap) + "@"
    compressed_data += str(times_amplified) + "@"
    compressed_data += str(tele_notes) + "@"
    compressed_data += str(coopertition) + "@"
    compressed_data += str(stage) + "@"
    compressed_data += str(harmony) + "@"
    compressed_data += str(spotlight) + "@"
    if role is not None:
      compressed_data += role + "@"
    else:
      compressed_data += "None" + "@"
    #compressed_data += str(tier) + "@"
    compressed_data += notes

  # QR Code Formatting
  """
  qr = qrcode.QRCode(version=1, box_size=10, border=1)
  qr.add_data(compressed_data)
  qr.make(fit=True)
  qr_img = qrcode.make(compressed_data)
  image_stream = BytesIO()
  # QR Code image conversion to base64
  qr_img.save(image_stream, format='PNG')
  image_stream.seek(0)
  image_data = base64.b64encode(image_stream.getvalue()).decode('utf-8')
  
  # This line prevents placeholder data from being entered into the google sheets as an entry
  if (compressed_data != "placeholder data"):
    update_google_sheet(compressed_data)
    set_averages("T", 5, split_data)
    set_averages("U", 8, split_data)
  sort_google_sheets()
  sort works but is very slow - just manually sort it lazy >:(
  """

  return render_template('scout.html',
                         qr_image=image_data,
                         all_teams=all_teams, )

# Download the offline program demos for scouts. Probably not useful, you can delete. I just commented out to preserve it. I have also commented out the link to the offline program in the dropdown menu, you can edit it in base.html
"""
@auth.route('/program')
def download_offline():
  return render_template(
    'program.html',
    attachment_filename=
    'website/static/FrcOfflineProgramDemo.FrcOfflineProgramDemo.zip')
"""

#@auth.route('/download')
#def download():
# return render_template('download.html')
