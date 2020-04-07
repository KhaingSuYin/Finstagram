#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

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

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
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
        cursor.execute(ins, (username, password, firstName,\
               lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    #Display photos
    #Shared with FriendGroup Union Seen by Followers
    query = 'SELECT postingDate, poster, pID, caption, photo.filePath, allFollowers \
             FROM photo Natural Join sharedwith Natural Join belongto \
             WHERE username = %s \
             UNION \
             SELECT postingDate, poster, pID, caption, photo.filePath, allFollowers \
             From photo Join follow On (photo.poster = follow.followee)\
             WHERE (follower = %s AND followStatus = 1) ORDER BY postingDate DESC'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, posts=data)

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/select_blogger')
def select_blogger():
    #check that user is logged in
    #username = session['username']
    #should throw exception if username not found
    
    cursor = conn.cursor();
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)

@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)

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
