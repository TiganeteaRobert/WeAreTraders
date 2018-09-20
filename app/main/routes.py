from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from werkzeug.utils import secure_filename
from app import db
from app.main.forms import EditProfileForm, PostForm, PostReviewForm
from app.models import User, Post, Review
from app.translate import translate
import os
from app.main import bp
import json
import requests
from flask import current_app, jsonify
from app.editprofile import editprofile


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    posts = Post.query.limit(current_app.config['POSTS_PER_PAGE']).all()
    return render_template('explore.html', title=_('Explore'),
                           posts=posts)

@bp.route('/add_listing', methods=['GET', 'POST'])
@login_required
def addlisting():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        f = form.picture.data
        post = Post(title=form.title.data, body=form.post.data,category=form.category.data, price=form.price.data, author=current_user,
                    language=language)
        db.session.add(post)
        db.session.commit()
        f.filename=(str(post.id) + '.jpg')
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], str(f.filename)))
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    return render_template('addlisting.html', title=_('Add Listing'),
                           form=form)

@bp.route('/removelisting/<id>', methods=['GET', 'POST'])
@login_required
def removelisting(id):
    post = Post.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('main.index'))
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/addreview', methods=['GET', 'POST'])
@login_required
def addreview(username):
    form = PostReviewForm()
    user = User.query.filter_by(username=username).first_or_404()
    if form.validate_on_submit():
        review = Review(body=form.body.data, title=form.title.data, rating=form.rating.data, reviewed_user=user.username, review_author=current_user.username)
        db.session.add(review)
        db.session.commit()
        flash(_('Your review is now live!'))
        return redirect(url_for('main.user', username=username))
    return render_template('addreview.html', title=_('Add Review'),
                           form=form)

@bp.route('/user/<username>/reviews')
@login_required
def reviews(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(reviewed_user=username).order_by(Review.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.reviews', username=user.username,
                       page=reviews.next_num) if reviews.has_next else None
    prev_url = url_for('main.reviews', username=user.username,
                       page=reviews.prev_num) if reviews.has_prev else None
    return render_template('reviews.html', reviews=reviews.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    form = EditProfileForm(username)
    user = User.query.filter_by(username=username).first_or_404()
    userdata = {'username':user.username, 'about_me':user.about_me}
    userdump = json.dumps(userdata)
    if form.validate_on_submit():
        user.username = form.username.data
        user.about_me = form.about_me.data
        db.session.commit()
        userdata = {'username':user.username, 'about_me':user.about_me}
        userdump = json.dumps(userdata)
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, form=form, userdump = userdump,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/category/<category>')
@login_required
def categorypage(category):
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(category=category).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.categorypage', category=category,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.categorypage', category=category,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('category.html', posts=posts.items)

@bp.route('/post/<postid>')
@login_required
def postpage(postid):
    post = Post.query.filter_by(id=postid).first_or_404()
    return render_template('postpage.html', post=post)


@bp.route('/showmore', methods=['GET','POST'])
@login_required
def showmore():
    data = request.get_json(force=True)
    a = slice(int(data['nrofposts']),int(data['nrofposts']) + 5)
    postlist = Post.query.all()[a]
    posts = []
    for post in postlist:
        posts.append(post.todict())
    posts = {'posts':posts}
    posts = json.dumps(posts)
    return posts

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})

