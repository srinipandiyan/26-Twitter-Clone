"""Testing Message model"""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase

from models import db, User, Message, Likes

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


class MessageModelTestCase(TestCase):
    """Test views for messages"""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.uid = 94566
        u = User.signup("test_user", "test@email.com", "password", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)
        
        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    

    def test_message_model(self):
        """Does basic message model work?"""

        message = Message(
            text="This is a test warble",
            user_id=self.u.id
        )

        db.session.add(message)
        db.session.commit()

        #Assert that the message has the correct attributes
        self.assertEqual(self.u.messages[0].text, "This is a test warble")
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(message.user_id, self.u.id)

    def test_message_likes(self):
        """Does message liking work?"""

        m1 = Message(
            text="This is a test warble",
            user_id=self.u.id
        )

        m2 = Message(
            text="Another test warble",
            user_id=self.u.id 
        )

        user = User.signup("test_user_123", "anothertest@email.com", "password", None)
        uid = 123
        user.id = uid
        db.session.add_all([m1, m2, user])
        db.session.commit()

        user.likes.append(m1)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == uid).all()

        #Assert that the message interactions yield the correct attributes
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, m1.id)
        
        #Check that the user's liked messages include m1
        self.assertEqual(len(user.likes), 1)
        self.assertEqual(user.likes[0].id, m1.id)