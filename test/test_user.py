"Test user API."

import http.client

import base


class User(base.Base):
    "Test the user API endpoints."

    def test_data(self):
        "Get user JSON."
        url = f"{base.CONFIG['root_url']}/user/{base.CONFIG['username']}"
        response = self.session.get(url)
        user = self.check_schema(response)


if __name__ == '__main__':
    base.run()
