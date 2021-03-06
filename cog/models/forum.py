'''
CoG forum models.

@author: Luca Cinquini
'''

from django.db import models
from constants import APPLICATION_LABEL
from project import Project
from django.contrib.auth.models import User
from topic import Topic
from django_comments.models import Comment
from django_comments.moderation import CommentModerator, moderator
from cog.notification import notify
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
import re

class Forum(models.Model):
    '''Top-level forum specific to each project, contains one or more Discussion.'''

    project = models.OneToOneField(Project, blank=False, related_name='forum')
        
    def __unicode__(self):
        return "%s Forum" % self.project.short_name
        
    class Meta:
        app_label= APPLICATION_LABEL
        
class ForumTopic(models.Model):
    '''Categories to group forum threads.'''
    
    forum = models.ForeignKey(Forum, blank=False, related_name='topics')
    title = models.CharField(max_length=200, verbose_name='Title', blank=False)
    description = models.TextField(verbose_name='Description', blank=True)
    author = models.ForeignKey(User, related_name='forum_topics', verbose_name='Author', blank=False, null=True, on_delete=models.SET_NULL)
    create_date = models.DateTimeField('Date Created', auto_now_add=True)
    update_date = models.DateTimeField('Date Updated', auto_now=True)
    # public/private flag: discussion can only be viewed by project members
    is_private = models.BooleanField(verbose_name='Private?', default=False, null=False)
    # order of topic within forum (for later reordering)
    order = models.IntegerField(blank=True, null=False, default=0)
    
    def getProject(self):
        return self.forum.project
    
    def get_threads(self):
        return ForumThread.objects.filter(topic=self).order_by("title")
    
    def __unicode__(self):
        return self.title
    
    class Meta:
        app_label= APPLICATION_LABEL
        
class ForumThread(models.Model):
    '''Group of forum posting about a specified topic.'''
    
    topic = models.ForeignKey(ForumTopic, blank=False, related_name='threads')
    author = models.ForeignKey(User, related_name='threads', verbose_name='Author', blank=False, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, verbose_name='SubTitle', blank=False)
    create_date = models.DateTimeField('Date Created', auto_now_add=True)
    update_date = models.DateTimeField('Date Updated', auto_now=True)
    
    def getProject(self):
        return self.topic.forum.project
            
    def get_comments(self):
        '''Method to retrieve all comments for this object.
           Needed to because comments must be explicitly deleted.'''
        
        content_type = ContentType.objects.get_for_model(ForumThread)
        return Comment.objects.filter(content_type=content_type).filter(object_pk=self.id).order_by('-submit_date')
    
    def get_last_comment(self):
        '''Returns the last comment for this object.'''
        
        try:
            return self.get_comments()[0]
        except IndexError:
            return None
    
    def __unicode__(self):
        return self.title

    class Meta:
        app_label= APPLICATION_LABEL    
        
class ForumModerator(CommentModerator):
    '''Custom comment moderator class that sends email to project administrators.'''
    
    email_notification = True
    
    def email(self, comment, content_object, request):
        
        thread = comment.content_object
        project = thread.getProject()
                
        # check project forum notification flag
        if project.forumNotificationEnabled:
        
            # build email
            user = comment.user
            
            subject = "[%s] Forum posting" % project.short_name
            # thread url: http://localhost:8000/projects/TestProject/thread/2/
            url = reverse('thread_detail', kwargs={ 'project_short_name':project.short_name.lower(), 'thread_id':thread.id })
            url = request.build_absolute_uri(url)        
            # specific comment url: http://localhost:8000/projects/TestProject/thread/2/?c=17
           
            # a) send plain text email
            #message = "User: %s\n Thread: %s\n Comment: %s\n" % (user, url, comment.comment)
            
            # b) send html formatted email
            # parse comment content to build images full URLs
            message = comment.comment
            # src="/site_media/projects/testproject/Unknown.jpeg"
            groups = list( re.finditer('src=\"[^\"]+\"', message) )
            paths = [] # list of (relpath, abspath) to replace after the full message is parsed
            for group in groups:
                relpath = message[group.start()+5:group.end()-1]
                abspath = request.build_absolute_uri(relpath)
                paths.append( (relpath, abspath) )
            # replace all
            for path in paths:
                message = message.replace(path[0], path[1])
            
            message = "User: %s<br/>Forum Thread: %s<p/>New Comment: %s" % (user, url, message)
    
            # send email                
            for admin in project.getAdminGroup().user_set.all():
                notify(admin, subject, message, mime_type='html')

moderator.register(ForumThread, ForumModerator)    
