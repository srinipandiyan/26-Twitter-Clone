"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        self.client = app.test_client()

        self.testuser = User.signup(username="test_user",
                                    email="test@email.com",
                                    password="password",
                                    image_url=None)
        self.testuser_id = 654789
        self.testuser.id = self.testuser.id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            response = c.post("/messages/new", data={"text": "Test Message"})

            # Make sure it redirects
            self.assertEqual(response.status_code, 302)

            #Make sure the message contains the correct text
            message = Message.query.one()
            self.assertEqual(message.text, "Test Message")


    def test_add_without_session(self):
        with self.client as c:
            response = c.post("/messages/new", data={"text": "Test Message"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

    def test_add_invalid_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 987123 # user does not exist in database

            response = c.post("/messages/new", data={"text": "Test Message"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))
    
    def test_message_show(self):

        message = Message(
            id=123,
            text="This is a test message",
            user_id=self.testuser_id
        )
        
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            message = Message.query.get(1234)

            response = c.get(f'/messages/{message.id}')

            self.assertEqual(response.status_code, 200)
            self.assertIn(message.text, str(response.data))

    def test_invalid_message_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            response = c.get('/messages/qwerty')

            self.assertEqual(response.status_code, 404)

    def test_message_delete(self):

        message = Message(
            id=123,
            text="this is a test message",
            user_id=self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/messages/123/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            message = Message.query.get(123)
            self.assertIsNone(message)

    def test_unauthorized_message_delete(self):

        # Unauthorized user attempts to delete the message
        user = User.signup(username="unauthorized",
                        email="unauthorized@email.com",
                        password="password",
                        image_url=None)
        user.id = 4567

        #Message is owned by testuser
        message = Message(
            id=123,
            text="This is a test message",
            user_id=self.testuser_id
        )
        db.session.add_all([user, message])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 4567

            response = c.post("/messages/123/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

            message = Message.query.get(123)
            self.assertIsNotNone(message)

    def test_message_delete_no_authentication(self):

        message = Message(
            id=123,
            text="This is a test message",
            user_id=self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            response = c.post("/messages/123/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

            message = Message.query.get(123)
            self.assertIsNotNone(message)