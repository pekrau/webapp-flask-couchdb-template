"Test root API."

import http.client

import base


class Root(base.Base):
    "Test the root API endpoint."

    def test_data(self):
        "Get API root JSON."
        url = f"{base.CONFIG['root_url']}"
        response = self.session.get(url)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
