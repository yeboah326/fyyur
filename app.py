# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from email.policy import default
import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
)
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from sys import exc_info
from pprint import pprint
from datetime import datetime
from models import db, Artist, Show, Venue
from typing import List

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app=app, db=db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------
@app.route("/venues")
def venues():
    unique_venues = [
        venue
        for venue in db.session.query(Venue)
        .distinct(Venue.state, Venue.city)
        .all()
    ]

    data = []

    for venue in unique_venues:
        data.append(
            {
                "city": venue.city,
                "state": venue.state,
                "venues": [
                    {
                        "id": next_venue.id,
                        "name": next_venue.name,
                        "num_upcoming_show": db.session.query(Show)
                        .filter(
                            Show.start_time
                            > datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
                        )
                        .count(),
                    }
                    for next_venue in db.session.query(Venue).filter(
                        Venue.state == venue.state, Venue.city == venue.city
                    )
                ],
            }
        )

    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    venues = (
        db.session.query(Venue)
        .filter(Venue.name.ilike(f"%{request.form.get('search_term')}%"))
        .all()
    )

    response = {
        "count": len(venues),
        "data": [
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": db.session.query(Show)
                .filter(
                    Show.start_time
                    > datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                )
                .count(),
            }
            for venue in venues
        ],
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue: Venue = Venue.query.filter_by(id=venue_id).first()

    past_shows = [
        show for show in venue.shows if show.start_time < datetime.now()
    ]

    upcoming_shows = [
        show for show in venue.shows if show.start_time > datetime.now()
    ]

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": json.loads(venue.genres),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [
            {
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for show in past_shows
        ],
        "upcoming_shows": [
            {
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for show in upcoming_shows
        ],
        "past_show_count": len(past_shows),
        "upcoming_show_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():

    form = VenueForm(request.form)

    try:
        if form.validate():
            venue = Venue(
                name=form.name.data,
                genres=json.dumps(form.genres.data),
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                website_link=form.website_link.data,
                facebook_link=form.facebook_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data,
            )

            db.session.add(venue)
            db.session.commit()

    except Exception:
        logging.warning(exc_info())
        flash(
            "An error occured"
            + request.form["name"]
            + " could not be listed successfully!"
        )
        db.session.rollback()

    else:
        flash("Venue " + request.form["name"] + " was successfully listed!")

    finally:
        db.session.close()

    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        db.session.delete(venue)
        db.session.commit()

    except:
        logging.warning(exc_info())
        flash("Venue deletion failed")
        db.session.rollback()

    else:
        flash("Venue was successfully deleted!")

    finally:
        db.session.close()

    return render_template("pages/home.html")

    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    data = [
        {
            "id": artist.id,
            "name": artist.name,
        }
        for artist in artists
    ]
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    artists = (
        db.session.query(Artist)
        .filter(Artist.name.ilike(f"%{request.form['search_term']}%"))
        .all()
    )

    response = {
        "count": len(artists),
        "data": [
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": db.session.query(Show)
                .filter(
                    Show.start_time
                    > datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                )
                .count(),
            }
            for artist in artists
        ],
    }
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist: Artist = Artist.query.filter_by(id=artist_id).first()

    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        if show.start_time > datetime.now():
            upcoming_shows.append(show)
        else:
            past_shows.append(show)

    data = {
        "id": artist_id,
        "name": artist.name,
        "genres": json.loads(artist.genres),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [
            {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for show in past_shows
        ],
        "upcoming_shows": [
            {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            for show in upcoming_shows
        ],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):

    artist: Artist = Artist.query.filter_by(id=artist_id).first()

    form = ArtistForm()

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = json.dumps(artist.genres)
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link
    form.seeking_venue.data = "y" if artist.seeking_venue else None
    form.seeking_description.data = artist.seeking_description

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.filter_by(id=artist_id).first()

        artist.name = request.form.get("name")
        artist.city = request.form.get("city")
        artist.state = request.form.get("state")
        artist.phone = request.form.get("phone")
        artist.genres = request.form.getlist("genres")
        artist.image_link = request.form.get("image_link")
        artist.facebook_link = request.form.get("facebook_link")
        artist.website_link = request.form.get("website_link")
        artist.seeking_venue = (
            True if request.form.get("seeking_venue") else False
        )
        artist.seeking_description = request.form.get("seeking_description")

        db.session.commit()

    except:
        logging.warning(exc_info())
        db.session.rollback()

    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue: Venue = Venue.query.filter_by(id=venue_id).first()

    form = VenueForm()

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.image_link.data = venue.image_link
    form.genres.data = json.dumps(venue.genres)
    form.facebook_link.data = venue.facebook_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    try:
        venue: Venue = Venue.query.filter_by(id=venue_id).first()
        venue.name = request.form.get("name")
        venue.city = request.form.get("city")
        venue.state = request.form.get("state")
        venue.address = request.form.get("address")
        venue.phone = request.form.get("phone")
        venue.image_link = request.form.get("image_link")
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = request.form.get("facebook_link")
        venue.website_link = request.form.get("website_link")
        venue.seeking_talent = (
            True if request.form.get("seeking_talent") else False
        )
        venue.seeking_description = request.form.get("seeking_description")

        db.session.commit()

    except:
        logging.warning(exc_info())
        db.session.rollback()

    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    form = ArtistForm(request.form)

    try:
        if form.validate():
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=json.dumps(form.genres.data),
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website_link=form.website_link.data,
                seeking_venue=form.seeking_venue.data,
                seeking_description=form.seeking_description.data,
            )

            db.session.add(artist)
            db.session.commit()

    except:
        logging.warning(exc_info())
        flash(
            "An error occured"
            + request.form["name"]
            + " could not be listed successfully!"
        )
        db.session.rollback()

    else:
        flash("Artist " + request.form["name"] + " was successfully listed!")

    finally:
        db.session.close()

    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = [
        {
            "venue_id": db.session.query(Venue)
            .filter(Venue.id == show.venue_id)
            .first()
            .id,
            "venue_name": db.session.query(Venue)
            .filter(Venue.id == show.venue_id)
            .first()
            .name,
            "artist_id": db.session.query(Artist)
            .filter(Artist.id == show.artist_id)
            .first()
            .id,
            "artist_name": db.session.query(Artist)
            .filter(Artist.id == show.artist_id)
            .first()
            .name,
            "artist_image_link": db.session.query(Artist)
            .filter(Artist.id == show.artist_id)
            .first()
            .image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        for show in db.session.query(Show).all()
    ]

    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm(request.form)
    try:
        if form.validate():
            show = Show(
                artist_id=form.artist_id.data,
                venue_id=form.venue_id.data,
                start_time=form.start_time.data,
            )

            db.session.add(show)
            db.session.commit()

    except:
        logging.warning(exc_info())
        flash("An error occurred while create show")
        db.session.rollback()

    else:
        flash("Show was successfully listed!")

    finally:
        db.session.close()

    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
