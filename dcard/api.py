# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import logging
from functools import partialmethod
from itertools import takewhile, count

from six.moves import zip

from dcard.utils import Client

logger = logging.getLogger(__name__)

DOMAIN = 'https://www.dcard.tw/'

forums_url = DOMAIN + '_api/forums'
post_url_pattern = DOMAIN + '_api/posts/{post_id}'
posts_meta_url_pattern = DOMAIN + '_api/forums/{forum}/posts'
post_links_url_pattern = DOMAIN + '_api/posts/{post_id}/links'
post_comments_url_pattern = DOMAIN + '_api/posts/{post_id}/comments'


class Api():

    metas_per_page = 30
    comments_per_page = 30

    def __init__(self, workers=8):
        self.client = Client(workers=workers)

    def get_all_forums(self):
        return self.client.get_json(route.forums())

    def get_general_forums(self):
        forums = self.client.get_json(route.forums())
        return [forum for forum in forums if not forum['isSchool']]

    def get_metas(self, name, sort, num, before, timebound=''):

        def filter_metas(metas):
            if num >= 0 and page == pages:
                metas = metas[:num - (pages - 1) * self.metas_per_page]
            if timebound:
                metas = [m for m in metas if m['updatedAt'] > timebound]
            return metas

        def eager_for_metas(bundle):
            page, metas = bundle
            if num >= 0 and page == pages + 1:
                return False
            if len(metas) == 0:
                logger.warning('[%s] 已到最末頁，第%d頁!', name, page)
            return len(metas) != 0

        def get_single_page_metas():
            while True:
                yield self.client.get_json(url, params=params)

        url = route.posts_meta(name)
        params = {'popular': 'true' if sort == 'popular' else 'false'}
        if before:
            params['before'] = before

        pages = -(-num // self.metas_per_page)

        paged_metas = zip(count(start=1), get_single_page_metas())

        for page, metas in takewhile(eager_for_metas, paged_metas):
            params['before'] = metas[-1]['id']
            metas = filter_metas(metas)
            if len(metas) == 0:
                return
            yield metas


class Route():

    host = 'https://www.dcard.tw/'

    def forums(self):
        return Route.host + '_api/forums'

    def posts_meta(self, forum):
        return Route.host + '_api/forums/{forum}/posts'.format(forum=forum)

    def post(self, post_id, addition=None):
        base = Route.host + '_api/posts/{id}'.format(id=post_id)
        if addition:
            return base + addition
        return base

    post_links = partialmethod(post, addition='links')
    post_comments = partialmethod(post, addition='comments')


route = Route()
api = Api()
