from django.contrib import admin
from cog.models import *
from django.shortcuts import get_object_or_404

class ProjectAdmin(admin.ModelAdmin):
    pass

admin.site.register(Project, ProjectAdmin)

class DocAdmin(admin.ModelAdmin):
    search_fields = ['title', 'path', 'description']
admin.site.register(Doc, DocAdmin)

class NewsAdmin(admin.ModelAdmin):

    fields = ('title', 'text')
    readonly_fields = ('author', 'project', 'other_projects')
    date_hierarchy = 'update_date'

    def save_model(self, request, obj, form, change):

        if (change==False):
            project_short_name = request.GET['project']
            project = get_object_or_404(Project, short_name__iexact=project_short_name)
            obj.author = request.user
            obj.project = project
            # must obtain a primary key first
            obj.save()
            for other_project_short_name in request.GET.getlist('other_projects'):
                other_project = get_object_or_404(Project, short_name__iexact=other_project_short_name)
                obj.other_projects.add(other_project)
                obj.save()
        else:
            obj.save()

admin.site.register(News, NewsAdmin)

class PostAdmin(admin.ModelAdmin):
    pass
admin.site.register(Post, PostAdmin)

admin.site.register(Topic, admin.ModelAdmin)

admin.site.register(SearchFacet, admin.ModelAdmin)
admin.site.register(SearchProfile, admin.ModelAdmin)

admin.site.register(Folder, admin.ModelAdmin)

admin.site.register(Bookmark, admin.ModelAdmin)

admin.site.register(Lock, admin.ModelAdmin)

admin.site.register(ProjectTag, admin.ModelAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
admin.site.register(UserProfile, UserProfileAdmin)

admin.site.register(PeerSite, admin.ModelAdmin)

admin.site.register(DataCart, admin.ModelAdmin)

admin.site.register(Permission, admin.ModelAdmin)

admin.site.register(ManagementBodyPurpose, admin.ModelAdmin)

admin.site.register(Forum, admin.ModelAdmin)

admin.site.register(ForumTopic, admin.ModelAdmin)

admin.site.register(ForumThread, admin.ModelAdmin)