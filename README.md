# Simple REST API based social network
_Tradecore interview assignment._

Sorry for the rushed readme; will get around to providing more context.

# Preparation
Consider using a virtualenv.
To run and test, install the development requirements:

    pip install -r requirements.dev.txt

To run the database, you can rely on docker compose:

    docker-compose up -d

Exclude -d if you want to be able to shutdown the database container with `<C-c>`

`docker-compose.yml` is fairly easy to read, if you're interested in reconfiguring the containerized database.

Run the database migrations:

    python manage.py migrate

# Running

And you're all set, you can run the development server:

    python manage.py runserver

The browsable api is enabled and can be found at `/api/v1`.
The API is HATEOAS based, so some interaction might be possible directly from the browsable API.
Unfortunately this is not as flexible as can be, and some routes, like the like-post creation route has to be manually posted.

To execute the bot for the demonstration

    python manage.py bot --config bot/config.yml http://<host>:<port>

# Testing

To run the provided tests:

    pytest
