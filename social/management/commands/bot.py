import argparse
import asyncio
import itertools
import random

import aiohttp
import factory
import yaml
from django.core.management.base import BaseCommand
from rest_framework import status

from social.factories import UserFactory, PostFactory


class Command(BaseCommand):
    help = 'Executes a bot run according to the config.'

    def add_arguments(self, parser):
        parser.add_argument('hostname', type=str)
        parser.add_argument('-c', '--config', required=False, default='config.yml', type=str)

    async def signup(self, user):
        """
        Sign up a user.
        """
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{self.options["hostname"]}/api/v1/user/?bot=true', data=user) as response:
                    data = await response.json()
                    assert response.status == status.HTTP_201_CREATED, f"Response {data}."

                    # since the response's password is readonly, include it
                    data['password'] = user['password']

                    return data

    async def login(self, user):
        """
        Retrieve the token for the provided user.
        """
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                # NOTE: The aiohttp library provides post and get as context managers, and I have no preferred style for
                #       writting multiline with statements. The choice of aiohttp over requests was solely to toy around
                #       with asynchronous programming in python.
                async with session.post(f'{self.options["hostname"]}/api/v1/login/',
                                        data={
                                            'username': user['username'],
                                            'password': user['password']
                                        }) as response:
                    data = await response.json()
                    assert response.status == status.HTTP_200_OK
                    assert 'token' in data

                    return {'instance': user, 'headers': {'Authorization': f'JWT {data["token"]}'}}

    async def post(self, user, post):
        """
        Post a random post on the behalf of a provided token.
        """
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{self.options["hostname"]}/api/v1/post/',
                                        data=post,
                                        headers=user['headers']) as response:
                    data = await response.json()
                    assert response.status == status.HTTP_201_CREATED, f'Returned status was {response.status}. Data {data}'

                    return data

    async def get_posts_with_no_likes(self):
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{self.options["hostname"]}/api/v1/post/?n_likes=0') as response:
                    posts = await response.json()
                    assert response.status == status.HTTP_200_OK
                    return posts

    async def like_post(self, user, post_url):
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                async with session.get(post_url, headers=user['headers']) as response:
                    post = await response.json()
                    assert response.status == status.HTTP_200_OK

                async with session.post(post['like_action'], headers=user['headers']) as session:
                    data = await response.json()
                    assert response.status == status.HTTP_200_OK

    async def load_user(self, user):
        with await self.conn_sem:
            async with aiohttp.ClientSession() as session:
                async with session.get(user['user_url']) as response:
                    data = await response.json()
                    assert response.status == status.HTTP_200_OK

                    user['instance'] = data
                    return user

    async def main(self, loop):
        # build users

        # NOTE: An experiment in style: using lambdas to make comprehensions with complex calls more readable.
        build_user = lambda: factory.build(dict, user_profile=None, FACTORY_CLASS=UserFactory)
        users = [build_user() for _ in range(self.config['number_of_users'])]

        # step 1: perform signup
        # NOTE: Even though I'd prefer a map here, since it clarifies the goal more appropriately in my opinion,
        #       the community consensus seems to be that the list comprehensions are preferable. I do not 
        #       disagree with the particular style, so here goes
        # NOTE: Again, for the sakes of readability, we're shadowing the function name, as 
        response_futures = [self.signup(user) for user in users]

        # NOTE: we're asigning to user so we'd efficiently get the urls
        #       (e.g. as they come, not by zipping/mapping later)
        users = await asyncio.gather(*response_futures)

        # ...
        # robustness omitted for the sake of brevity
        # ...

        # step 1a: obtain login tokens
        login_futures = [self.login(user) for user in users]
        users = await asyncio.gather(*login_futures)

        # step 2: post, and do it in parallel
        post_futures = []
        for user in users:
            n_posts = random.randint(1, self.config['max_posts_per_user'])

            user['n_posts'] = n_posts

            for _ in range(n_posts):
                # the author is the authenticated user, pop it from the result
                post_dict = factory.build(dict, author=None, FACTORY_CLASS=PostFactory)
                post_dict.pop('author')

                post_futures.append(self.post(user, post_dict))

        await asyncio.gather(*post_futures)

        # step 3: like, simmer down, do it sequentialy
        # TODO: go nuclear and pre-calculate the like-path?

        # users with most posts like first
        users.sort(key=lambda user: user['n_posts'])

        posts = await self.get_posts_with_no_likes()
        target_users = [{'user_url': user_url, 'non_liked_post_urls': posts} for user_url, posts
                        in itertools.groupby(posts, lambda post: post['author'])]

        target_user_futures = [self.load_user(user) for user in target_users]
        target_users = await asyncio.gather(*target_user_futures)

        # A naive rule engine is specified in the like_generator.
        # NOTE: Handy property of the generator is that it will stop once StopIteration gets raised, which can be either
        #       once we exhaust likes, or once the rule of no-users-left-unliked comes into effect.
        like_futures = [self.like_post(**like_dict) for like_dict in self.like_generator(users, target_users)]
        # ^^^^^^^^^^
        # TODONE: went nuclear and essentially pre-calculated the like-path
        await asyncio.gather(*like_futures)

    def like_generator(self, users, target_users):
        """
        The generator runs sequentially and handles liking rules.
        Input data should be sufficient to calculate the like-path without additional API requests.
        Basically a naive DoS planner.
        """
        for user in users:
            likes = 0

            while(likes < self.config['max_likes_per_user']):
                # make sure the post doesn't belong to the current user
                # NOTE: for whatever reason, I prefer filtering over generator comprehensions, kind of gives me the idea
                #       what's going on just a tad bit faster.
                random.shuffle(target_users)
                other_users = filter(lambda target_user: target_user['user_url'] != user['instance']['url'],
                                     target_users)

                # will implicitly raise StopIterations if no users meeting criteria are found.
                # this essentialy enforces the last rule, that if there are no posts with zero likes, the process stops
                # the convoluted part: it checks that no _users_ with zero-like-posts exist
                # TODO: abide to the zen of python, be more explicit
                target_user = next(other_users)

                # get an arbitrary post
                post = random.choice(target_user['instance']['posts'])

                if post in target_user['non_liked_post_urls']:
                    target_user['non_liked_post_urls'].remove(post)

                    if len(target_user['non_liked_post_urls']) == 0:
                        target_users.remove(target_user)

                yield {'user': user, 'post_url': post}

                likes += 1

    def handle(self, *args, **options):
        self.options = options

        with open(options['config'], 'r') as f:
            self.config = yaml.load(f)

        self.conn_sem = asyncio.Semaphore(20)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main(loop))

