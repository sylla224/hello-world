from flask import Blueprint, render_template, session, redirect, url_for, current_app, request, flash, Response
from app.models import User, Participants, Winner, Archive, WinnerArchive
from app.auth.views import current_user, get_current_user
from app.auth.forms import LoginForm
import os, time, random, io
import xlwt
from app import db
import pandas as pd

main = Blueprint('main', __name__, template_folder='templates')

@main.route('/')
def home():
    if request.cookies.get("user_id"):
        form = LoginForm()
        #current_user = get_current_user()
        return render_template("home.html", form=form)
    return redirect(url_for('auth.login'))

# Get the uploaded files
@main.route("/upload", methods=['POST'])
def uploadFiles():
    if request.cookies.get("user_id"):
        # get the uploaded file
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_path)
            participant = Participants.query.all()
            winner = Winner.query.all()
            for row in participant:
                archive = Archive(row.visionOuc, row.oucDescription, row.schemeCode, row.accountNo, row.accountName, row.accountOpenDate, row.phoneNumber)
                db.session.add(archive)
                db.session.query(Participants).delete()
                db.session.query(Winner).delete()
                db.session.commit()
            parseCSV(file_path)
        return redirect(url_for('main.getParticipants'))
    return redirect(url_for('auth.login'))


def parseCSV(filePath):
    # CVS Column Names
    col_names = ['visionOuc', 'oucDescription', 'schemeCode', 'accountNo', 'accountName', 'accountOpenDate', 'phoneNumber']
    # Use Pandas to parse the CSV file
    csvData = pd.read_csv(filePath, names=col_names, sep=';', header=0)
    # Loop through the Rows
    for i, row in csvData.iterrows():
        participant = Participants(row['visionOuc'], row['oucDescription'], row['schemeCode'], row['accountNo'], row['accountName'], row['accountOpenDate'], row['phoneNumber'])
        db.session.add(participant)
        db.session.commit()

ROWS_PER_PAGE = 5

@main.route('/paritcipant')
def getParticipants():
    if request.cookies.get("user_id"):
        # Set the pagination configuration
        page = request.args.get('page', 1, type=int)

        data = Participants.query.paginate(page=page, per_page=ROWS_PER_PAGE)
        if data:
            return render_template('listParticipants.html', data=data)
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))

@main.route('/download')
def downloadReport():
    liste = []
    if request.cookies.get("user_id"):
        data = Winner.query.all()

        output = io.BytesIO()
        workbook = xlwt.Workbook()
        sh = workbook.add_sheet('Vainqueur')

        sh.write(0, 0, 'VISION_OUC')
        sh.write(0, 1, 'OUC_DESCRIPTION')
        sh.write(0, 2, 'SCHEME_CODE')
        sh.write(0, 3, 'ACCOUNT_NO')
        sh.write(0, 4, 'ACCOUNT_NAME')
        sh.write(0, 5, 'ACCOUNT_OPEN_DATE')
        sh.write(0, 6, 'PHONE_NUMBER')

        idx = 0
        for item in data:
            sh.write(idx + 1, 0, item.visionOuc)
            sh.write(idx + 1, 1, item.oucDescription)
            sh.write(idx + 1, 2, item.schemeCode)
            sh.write(idx + 1, 3, item.accountNo)
            sh.write(idx + 1, 4, item.accountName)
            sh.write(idx + 1, 5, item.accountOpenDate)
            sh.write(idx + 1, 6, item.phoneNumber)
            idx += 1

        workbook.save(output)
        output.seek(0)

        return Response(output, mimetype="application/ms-excel",
                        headers={"Content-Disposition": "attachement;filename=Vainqueurs.xls"})
    return redirect(url_for('auth.login'))

@main.route('/winner')
def getWinner():
    if request.cookies.get("user_id"):
        # Set the pagination configuration
        page = request.args.get('page', 1, type=int)

        data = Winner.query.paginate(page=page, per_page=ROWS_PER_PAGE)
        if data:
            return render_template('listWinner.html', data=data)
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))

@main.route('/selectWinner', methods=['POST'])
def winner():
    my_list = []
    list_winner = []
    liste = []
    if request.cookies.get("user_id"):
        time.sleep(30)
        data = Participants.query.all()
        my_list = [row.accountNo for row in data]
        elt = random.choice(my_list)
        winner = Participants.query.filter_by(accountNo=elt).first()
        data_winner = Winner(winner.visionOuc, winner.oucDescription, winner.schemeCode, winner.accountNo, winner.accountName, winner.accountOpenDate, winner.phoneNumber)
        winnerArchive = WinnerArchive(winner.visionOuc, winner.oucDescription, winner.schemeCode, winner.accountNo, winner.accountName, winner.accountOpenDate, winner.phoneNumber)
        db.session.add(data_winner)
        db.session.add(winnerArchive)
        db.session.query(Participants).filter_by(accountNo=elt).delete()
        db.session.commit()
        flash('Le Numéro de  compte ' + winner.accountNo + ' a été selectionné')
        return redirect(url_for('main.getParticipants'))
    return redirect(url_for('auth.login'))


# @main.route('/')
# def home():
# 	users = User.query.all()
# 	return render_template('home.html', users=users)
