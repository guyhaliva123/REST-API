from flask.views import MethodView
from flask_smorest import Blueprint,abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token,jwt_required,get_jwt

from db import db
from blocklist import BLOCKLIST
from models import UserModel
from schemas import UserSchema

blp = Blueprint("Users","users",description="Operations on users")

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserSchema)
    # user_data it is all the data that comes in JSON from the api request.
    def post(self,user_data):
        # check if the user is not already exists.
        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="A user with that username is already exists.")

        user = UserModel(
            username = user_data["username"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )
        db.session.add(user)
        db.session.commit()

        return {"message":"user created successfully."},201
    

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self,user_data):
        user = UserModel.query.filter(UserModel.username == user_data["username"]).first()
        # the verify method take the password recived from the client hash it and after hashing it
        # ,it will check if its equal to the hashed password in the database.
        if user and pbkdf2_sha256.verify(user_data["password"] ,user.password):
            # were gonna pass the user id to be stored inside the access token.
            access_token = create_access_token(identity=user.id)
            return {"access_token":access_token}
        abort(401, message="Invalid credentials.")


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message":"successfully logged out."}


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200,UserSchema)
    def get(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        return user
    
    def delete(self,user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message":"User deleted."},200
