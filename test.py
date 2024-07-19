import unittest
from app import create_app
from config import TestConfig
from database import db
from models import User
from mapper.UserMapper import get_all_users, create_user


class TestQueries(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        user = create_user('testuser', 'testuser@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')

    def test_get_all_users(self):
        create_user('testuser1', 'testuser1@example.com')
        create_user('testuser2', 'testuser2@example.com')
        users = get_all_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].username, 'testuser1')
        self.assertEqual(users[1].username, 'testuser2')


if __name__ == '__main__':
    unittest.main()
