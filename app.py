import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import urllib.request

if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# Routes

@app.route('/file/<filename>')
def file(filename):
    return mongo.send_file(filename)


@app.route("/")
@app.route("/home")
def home():
    books = list(mongo.db.Books.find().sort("_id", -1).limit(15))
    return render_template("home.html", books=books)


@app.context_processor
def inject_user():
    categories = list(mongo.db.category.find())
    return dict(categories=categories)


@app.context_processor
def inject_user():
    best_selling = "yes"
    selling = list(mongo.db.Books.find(
        {'book_best_selling': best_selling}).sort("_id", -1).limit(8))
    return dict(selling=selling)


@app.context_processor
def inject_user():
    discount = list(mongo.db.Books.find().sort("_id", 1).limit(8))
    return dict(discount=discount)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                session["role"] = existing_user["role"]
                if session["role"] == "admin":
                    return redirect(url_for(
                        "profile", username=session["user"]))
                else:
                    return redirect(url_for(
                        "home", username=session["user"]))

            else:
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))
        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    session.pop("role")

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        user_role = "admin" if request.form.get("customSwitch1") else "user"
        register = {
            "role": user_role,
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "email": request.form.get("email").lower(),
            "address": request.form.get("address").lower(),
            "postal": request.form.get("postal").lower()

        }
        mongo.db.users.insert_one(register)
        flash("Registration Successful!")

        return render_template("login.html")
    return render_template("register.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    user = mongo.db.users.find_one(
        {"username": session["user"]})
    if session["user"]:
        return render_template("profile.html", user=user)


@app.route("/category_display/<value_id>", methods=["GET", "POST"])
def category_display(value_id):

    category_id = mongo.db.category.find_one({"_id": ObjectId(value_id)})
    category_book_value = list(mongo.db.Books.find(
        {'book_category_id': category_id['_id']}))
    return render_template("category_display.html", category_table=category_id, category_book=category_book_value)


APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route("/admin_book_insert", methods=["GET", "POST"])
def admin_book_insert():
    if request.method == "POST":
        existing_book = mongo.db.Books.find_one(
            {"book_title": request.form.get("book_title").lower()})
        if existing_book:
            flash("This Book is already there")
            return redirect(url_for("admin_book_insert"))

        target = os.path.join(APP_ROOT, 'static/')
        print(target)
        if not os.path.isdir(target):
            os.mkdir(target)
        else:
            print("couldn't create upload directory {}".format(target))
        print(request.files.getlist("file"))
        for upload in request.files.getlist("file"):
            print(upload)
            print("{} is the file name  ".format(upload.filename))
            filename = upload.filename
            destination = "/".join([target, filename])
            print("accepts incoming file:", filename)
            print("save it to :", destination)
            upload.save(destination)

            book = {
                "book_title": request.form.get("book_title").lower(),
                "book_publisher_id": ObjectId(request.form.get("publisher_name").lower()),
                "book_author_id": ObjectId(request.form.get("author_name").lower()),
                "book_category_id": ObjectId(request.form.get("category_name").lower()),
                "book_availabilty": request.form.get("book_availabilty").lower(),
                "book_discount": request.form.get("book_discount").lower(),
                "book_best_selling": request.form.get("book_best_selling").lower(),
                "book_price": request.form.get("book_price").lower(),
                "book_pages": request.form.get("book_pages").lower(),
                "book_img": filename
            }
            mongo.db.Books.insert_one(book)
            flash('successfully Inserted')
            return redirect(url_for("managebooks"))

    cat = mongo.db.category.find().sort("category_name", 1)
    author = mongo.db.author.find().sort("author_name", 1)
    publisher = mongo.db.publisher.find().sort("publisher_name", 1)
    return render_template("admin_book_insert.html", cat=cat, publishers=publisher, authors=author)


@app.route("/managepublisher")
def managepublisher():
    publisher = list(mongo.db.publisher.find())
    return render_template("managepublisher.html", publisher=publisher)


@app.route("/publisherregister", methods=["GET", "POST"])
def publisherregister():
    if request.method == "POST":
        existing_user = mongo.db.publisher.find_one(
            {"publisher_name": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("publisherregister"))
        register = {
            "publisher_name": request.form.get("username").lower(),

        }
        mongo.db.publisher.insert_one(register)
        flash("Registration Successful!")
        return redirect(url_for("managepublisher"))

    return render_template("publisherregister.html")


@app.route("/delete_publisher/<publisher_id>")
def delete_publisher(publisher_id):
    mongo.db.publisher.remove({"_id": ObjectId(publisher_id)})
    flash("Successfully Deleted")
    return redirect(url_for("managepublisher"))


@app.route("/manageauthor")
def manageauthor():
    author = list(mongo.db.author.find())
    return render_template("manageauthor.html", author=author)


@app.route("/authorregister", methods=["GET", "POST"])
def authorregister():
    if request.method == "POST":
        existing_user = mongo.db.author.find_one(
            {"author_name": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("authorregister"))
        register = {
            "author_name": request.form.get("username").lower(),

        }
        mongo.db.author.insert_one(register)
        flash("Registration Successful!")
        return redirect(url_for("manageauthor"))

    return render_template("authorregister.html")


@app.route("/delete_author/<author_id>")
def delete_author(author_id):
    mongo.db.author.remove({"_id": ObjectId(author_id)})
    flash("Successfully Deleted")
    return redirect(url_for("manageauthor"))


@app.route("/managecategory")
def managecategory():
    category = list(mongo.db.category.find())
    return render_template("managecategory.html", category=category)


@app.route("/categoryregister", methods=["GET", "POST"])
def categoryregister():
    if request.method == "POST":
        existing = mongo.db.category.find_one(
            {"category_name": request.form.get("username").lower()})

        if existing:
            flash("Category already exists")
            return redirect(url_for("categoryregister"))
        register = {
            "category_name": request.form.get("username").lower(),

        }
        mongo.db.category.insert_one(register)
        flash("Category Added!")
        return redirect(url_for("managecategory"))

    return render_template("categoryregister.html")


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.category.remove({"_id": ObjectId(category_id)})
    flash("Successfully Deleted")
    return redirect(url_for("managecategory"))


@app.route("/manage_review")
def manage_review():
    reviews_all = mongo.db.book_reviews.find().sort("_id", -1)
    book_list = mongo.db.Books.find()
    return render_template("managereview.html", book_list=book_list, reviews=reviews_all)


@app.route("/managebooks")
def managebooks():
    book = list(mongo.db.Books.find())
    return render_template("managebooks.html", book=book)


@app.route("/book_update/<book_id>", methods=["GET", "POST"])
def book_update(book_id):
    if request.method == "POST":

        myquery = {"_id": ObjectId(book_id)}
        newvalues = {"$set": {"book_availabilty": request.form.get("book_availabilty"), "book_best_selling": request.form.get(
            "book_best_selling"), "book_discount": request.form.get("book_discount"), "book_price": request.form.get("book_price"), "book_pages": request.form.get("book_pages")}}

        mongo.db.Books.update(myquery, newvalues)
        flash("Book Successfully Updated")

        return redirect(url_for("managebooks"))
    updated = mongo.db.Books.find_one({"_id": ObjectId(book_id)})
    return render_template("book_update.html", updated=updated)


@app.route("/delete_book/<book_id>")
def delete_book(book_id):
    mongo.db.Books.remove({"_id": ObjectId(book_id)})
    flash("Successfully Deleted")
    return redirect(url_for("managebooks"))


@app.route("/seereviews/<book_id>", methods=["GET", "POST"])
def seereviews(book_id):

    book_id = mongo.db.Books.find_one({"_id": ObjectId(book_id)})
    review_book_value = list(mongo.db.book_reviews.find(
        {'book_id': book_id['_id'], 'review_status': "Approved"}))
    return render_template("reviews.html", book_id=book_id, reveiewd_book=review_book_value)


@app.route("/update_review/<review_id>", methods=["GET", "POST"])
def update_review(review_id):

    myquery = {"_id": ObjectId(review_id)}
    newvalues = {"$set": {"review_status": "Approved"}}
    flash("Successfully Updated")
    mongo.db.book_reviews.update(myquery, newvalues)

    return redirect(url_for("manage_review"))


@app.route("/postreview/<book_id>", methods=["GET", "POST"])
def postreview(book_id):

    if request.method == "POST":
        register = {
            "book_id": ObjectId(book_id),
            "book_review": request.form.get("review").lower(),
            "reviewed_by": session["user"],
            "review_status": "Not Approved"

        }
        mongo.db.book_reviews.insert_one(register)
        flash("Your Review Can Only Be Viewed Once It Is Approved By The Site Owner!")
        return redirect(url_for("home"))
    updated = mongo.db.Books.find_one({"_id": ObjectId(book_id)})
    return render_template("profile.html", updated=updated)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    books = list(mongo.db.Books.find({"$text": {"$search": query}}))
    return render_template("home.html", books=books)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
