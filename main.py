#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import webapp2
import os
import jinja2
import re
import time
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)




class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class BlogPost(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    postnum = db.StringProperty()



class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.redirect('/blog')



class BlogMainHandler(Handler):
    def render_front(self, posts=''):
        posts = db.GqlQuery('SELECT * FROM BlogPost ORDER BY created')
        for post in posts:
            logging.debug(post.subject)
        self.render('main.html', posts=posts)


    def get(self, trailingslash=None):
        self.render_front()



class NewPostHandler(Handler):
    def write_form(self, subject='', content='', error=''):
        self.render("newpost.html", subject=subject, content=content, error=error)

    def get(self, trailingslash=None):
        self.write_form()

    def post(self, otherarg):
        logging.debug(otherarg)
        subject = self.request.get("subject")
        content = self.request.get("content")
        logging.debug(subject)
        logging.debug(content)

        if subject and content:
            next_count = BlogPost.all().count() + 1
            postnum = '{num:04d}'.format(num=next_count)
            p = BlogPost(subject=subject, content=content, postnum=str(postnum))
            p.put()
            #id = p.key().id()
            url = '/blog/%s' % postnum
            self.redirect(url)
        else:
            error = "Please enter both title and content!"
            self.write_form(subject=subject, content=content, error=error)


class PermalinkHandler(Handler):
    def render_post(self, postnum=''):
        POST_RE = re.compile('[0-9]{4}$')
        postnum = re.search(POST_RE, self.request.path).group(0)
        logging.debug(postnum)
        #post_key = db.Key.from_path('BlogPost', postnum)
        #post = db.get(post_key)
        try:
            posts = BlogPost.all().filter("postnum =", postnum)
            self.render("singlepost.html", post=posts[0])
        except IndexError:
            time.sleep(0.1)
            posts = BlogPost.all().filter("postnum =", postnum)
            self.render("singlepost.html", post=posts[0])

    def get(self, postnum=None, trailingslash=None):
        self.render_post(postnum=postnum)


app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=MainHandler),
    webapp2.Route(r'/blog<:/?$>', handler=BlogMainHandler),
    webapp2.Route(r'/blog/newpost<:/?$>', handler=NewPostHandler),
    webapp2.Route(r'/blog/<:\d{4}><:/?$>', handler=PermalinkHandler)
], debug=True)

