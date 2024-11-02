import sqlite3
import datetime
from flask import Flask, render_template, request, url_for, flash, redirect, abort
from werkzeug.exceptions import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  

def get_db_connection():
    try:
        conn = sqlite3.connect('database.db', detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        
        # Register adapter for datetime
        def adapt_datetime(ts):
            return ts.isoformat()

        sqlite3.register_adapter(datetime.datetime, adapt_datetime)
        
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

@app.route('/')
def index():
    try:
        print("Accessing index route")
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed", 500
        
        posts = conn.execute('SELECT id, title, content, datetime(created) as created FROM posts ORDER BY created DESC').fetchall()
        conn.close()
        print(f"Found {len(posts) if posts else 0} posts")
        return render_template('index.html', posts=posts)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"An error occurred: {str(e)}", 500

@app.route('/post/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                        (title, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE posts SET title = ?, content = ?'
                        ' WHERE id = ?',
                        (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
