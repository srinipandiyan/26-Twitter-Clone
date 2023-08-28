"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client and add sample user."""
        db.drop_all()
        db.create_all()

        user1 = User.signup("test1", "test1@email.org", "randompassword", None)
        uid_1 = 24
        user1.id = uid_1

        user2 = User.signup("test2", "test2@email.com", "a_string", None)
        uid_2 = 12345
        user2.id = uid_2

        db.session.commit()

        user1 = User.query.get(uid_1)
        user2 = User.query.get(uid_2)

        self.user1 = user1
        self.uid_1 = uid_1

        self.user2 = user2
        self.uid_2 = uid_2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        user = User(
            email="test@testemail.com",
            username="testing_user",
            password="a_hashable_password"
        )

        db.session.add(user)
        db.session.commit()

        # Assert that user has no messages or followers on signup
        self.assertEqual(len(user.messages), 0)
        self.assertEqual(len(user.followers), 0)

    ####
    #
    # Following tests
    #
    ####
    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user1.following), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    ####
    #
    # Signup Tests
    #
    ####
    def test_valid_signup(self):
        u_test = User.signup("hello_test", "randomemail@email.com", "password", None)
        user_id = 5630
        u_test.id = user_id
        db.session.commit()

        u_test = User.query.get(user_id)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "hello_test")
        self.assertEqual(u_test.email, "randomemail@email.com")
        #testing hashing
        self.assertNotEqual(u_test.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid = User.signup(None, "ok@email.com", "password", None)
        uid = 321
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid = User.signup("test_username", None, "password", None)
        uid = 123789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("test_username", "ok@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("test_username", "ok@email.com", None, None)
    
    ####
    #
    # Authentication Tests
    #
    ####
    def test_valid_authentication(self):
        user = User.authenticate(self.user1.username, "randompassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.uid_1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("invalid_username", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.user1.username, "invalid_password"))