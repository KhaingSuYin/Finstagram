#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import random
import os, hashlib
from datetime import datetime

#Initialize the app from Flask
app = Flask(__name__, static_folder="images")

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3308,
                       user='root',
                       password='',
                       db='FlaskDemo',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    hashed = hashlib.md5(password.encode()).hexdigest()
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    hashed = hashlib.md5(password.encode()).hexdigest()
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO person (username, password, firstName,\
               lastName, email) VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed, firstName,\
               lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    return render_template('home.html', username=user)


#Define route to manage followers
@app.route('/manage')
def manageFollow():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT * FROM Follow WHERE followStatus = 0 AND followee = %s'
    cursor.execute(query, (username))
    requestData = cursor.fetchall()
    cursor.close()
    return render_template('manage.html', requestData = requestData)

#Let the user type in the username and find for user to follow
#Raise an error if username is invalid
@app.route('/searchFollow', methods = ["POST"])
def searchFollow():
    username = session['username']
    cursor = conn.cursor();
    followee = request.form["user"]
    query = 'SELECT username FROM person WHERE username = %s'
    cursor.execute(query, (followee))
    data = cursor.fetchall()
    if (data):
        query1 = 'INSERT INTO follow (follower, followee, followStatus) VALUES (%s, %s, %s)'
        cursor.execute(query1, (username, followee, 0))
        conn.commit()
        cursor.close()
        return render_template('home.html')
    else:
        error = "This friend group has already been created"
        return render_template('manage.html', error = error)
    
#Accept or Decline follow request
@app.route('/followRequest', methods = ["GET", "POST"])
def followRequest():
    username = session['username']
    followerName = request.form['follower']
    print(request.form["followButton"])
    if (request.form["followButton"] == "accept"):
        print ("ACCEPTED")
        updateQuery = 'UPDATE Follow SET followStatus = 1 WHERE followee = %s AND follower = %s'
        cursor = conn.cursor();
        cursor.execute(updateQuery, (username, followerName))

    elif (request.form["followButton"] == "decline"):
        print ("DECLINED")
        updateQuery = 'DELETE FROM Follow WHERE followee = %s'
        cursor = conn.cursor();
        cursor.execute(updateQuery, (username))
    else:
        print ("Some error occurs.")

    requestQuery = 'SELECT * FROM Follow WHERE followStatus = 0 AND followee = %s'
    cursor.execute(requestQuery, (username))
    requestData = cursor.fetchall()

    cursor.close()
    return render_template('manage.html', requestData = requestData)

#define route to manage and view posts
@app.route('/view_posts', methods = ['GET','POST'])
def view_posts():
    user = session['username']
    cursor = conn.cursor();
    #Display photos
    #Shared with FriendGroup Union Seen by Followers
    #followStatus = 0 -> rejected/ not accepted
    #followStatus = 1 -> accpeted
    query1 = 'SELECT postingDate, poster, pID, caption, filePath\
             FROM photo WHERE poster = %s UNION\
             SELECT postingDate, poster, pID, caption, photo.filePath\
             FROM photo Natural Join sharedwith Join belongto Using (groupName, groupCreator)\
             WHERE username = %s \
             UNION \
             SELECT postingDate, poster, pID, caption, photo.filePath\
             From photo Join follow On (photo.poster = follow.followee)\
             WHERE (follower = %s AND followStatus = 1) ORDER BY postingDate DESC'
    cursor.execute(query1, (user, user, user))
    data1 = cursor.fetchall()
    query2= 'SELECT tag.username as tagged, reactto.username as reacted, tag.pID as pID, comment, emoji\
             FROM tag JOIN reactto USING (pID) WHERE tagStatus = 1'
    cursor.execute(query2)
    data2 = cursor.fetchall()
    query3 = 'SELECT username, firstName, lastName FROM person'
    cursor.execute(query3)
    data3 = cursor.fetchall()
    cursor.close()
    cursor.close()
    return render_template('view_posts.html', username = user, posts=data1, tag_react = data2,user_list=data3 )

#get form to insert into photo
@app.route('/post_a_photo',methods=['GET', 'POST'])
def post_a_photo():
    username = session['username']
    cursor = conn.cursor();
    photo = os.path.join(APP_ROOT, 'images/')
    if not os.path.isdir(photo):
        os.mkdir(photo)
    filePath = request.files['file']
    photo1 = filePath.filename
    #filePath.save(os.path.join(photo, filePath.filename))
    destination = str('/'.join([photo, filePath.filename]))
    filePath.save(destination)
    caption = request.form['caption']
    allFollowers = request.form.get('allFollowers')
    if(allFollowers != 0):
        allFollowers = 1;
    query1 = 'INSERT INTO photo (pID, postingDate, filePath, allFollowers, caption, poster) VALUES(%s, %s, %s, %s, %s, %s)'
    photoID = random.randint(0,64)
    date = datetime.now();
    cursor.execute(query1, (photoID, date, photo1, allFollowers, caption, username))
    conn.commit()
    data1 = request.form.get('groups')
    if(data1 is not None):
        datalst = data1.split(",")
        query2 = 'INSERT INTO sharedwith(pID, groupName, groupCreator) VALUES (%s, %s, %s)'
        cursor.execute(query2, (photoID, datalst[0], datalst[1]))
        conn.commit()
    data2 = request.form.get('tags')
    if(data2 is not None):
        query3 = 'INSERT INTO tag(pID, username, tagStatus) VALUES (%s, %s, %s)'
        cursor.execute(query3, (photoID, data2, 0))
        conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#request data from user for new post        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    query1 = 'SELECT groupName, groupCreator FROM belongto JOIN friendgroup using (groupName, groupCreator) \
             WHERE username = %s'
    cursor.execute(query1, username)
    data1 = cursor.fetchall()
    query2 = 'SELECT DISTINCT username, firstName, lastName FROM person'
    cursor.execute(query2)
    data2 = cursor.fetchall()
    cursor.close()
    return render_template('post.html', visible_list = data1, taglist = data2)

#show all the posts from the selected user
@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    user = request.args.get('user')
    user = user[:-1]
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT postingDate, poster, pID, caption, photo.filePath\
             FROM photo WHERE poster = %s UNION\
             SELECT postingDate, poster, pID, caption, photo.filePath\
             From photo Join follow On (photo.poster = follow.followee)\
             WHERE (photo.poster = %s AND follower = %s AND followStatus = 1) ORDER BY postingDate DESC'
    cursor.execute(query, (user, user, username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', username=user, posts=data)

#direct to page to create friend group
@app.route('/friendgroup')
def friendgroup():
    return render_template('friendgroup.html')


#get info to create friend group
#check if it is valid and display eroor message if not
@app.route('/createFG', methods = ["GET"])
def createFG():
    username = session['username']
    cursor = conn.cursor();
    group = request.args["groupName"]
    descrip = request.args["description"]
    query = 'SELECT * FROM friendgroup WHERE groupName = %s AND groupCreator = %s'
    cursor.execute(query, (group,username))
    data = cursor.fetchall()
    if (data):
        error = "This friend group has already been created"
        return render_template('friendgroup.html', error = error)
    else:
        ins1 = 'INSERT INTO friendGroup (groupName, groupCreator, description) \
                 VALUES(%s, %s, %s)'
        cursor.execute(ins1, (group, username, descrip))
        conn.commit()
        ins2 = 'INSERT INTO belongto (username, groupName, groupCreator) VALUES (%s, %s, %s)'
        cursor.execute(ins2, (username, group, username))
        conn.commit()
        cursor.close()
        return render_template('home.html')

#add Reaction to a visible post
@app.route('/addReact', methods = ["POST"])
def addReact():
    username = session['username']
    cursor = conn.cursor();
    emoji = request.form["emoji"]
    comment = request.form["comment"]
    pID = request.form.get("pID")
    date = datetime.now()
    ins = 'INSERT INTO reactto (username, pID, reactionTime, comment, emoji) VALUES (%s, %s, %s, %s, %s)'
    cursor.execute(ins, (username, pID, date, comment, emoji))
    conn.commit()
    cursor.close()
    return render_template('home.html')


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
