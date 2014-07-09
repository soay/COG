from cog.models import *
from django.forms import ModelForm, ModelMultipleChoiceField, NullBooleanSelect
from django.db import models
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from django.forms import ModelForm, Textarea, TextInput, Select, FileInput, CheckboxSelectMultiple
from django.core.exceptions import ObjectDoesNotExist
from os.path import basename
import re
from cog.utils import *
from django.db.models import Q
from cog.forms.forms_image import ImageForm
from cog.utils import hasText


class ProjectForm(ModelForm):

    # note: alternative widget for peer selection would require additional js and css
    #peers = ModelMultipleChoiceField(Project.objects.all(),
    #        widget=FilteredSelectMultiple("Peer Projects", False, attrs={'rows':'10'}))

    # extra field not present in model, used for deletion of previously uploaded logo
    delete_logo = forms.BooleanField(required=False)
    # specify size of logo_url text field
    logo_url = forms.CharField(required=False, widget=TextInput(attrs={'size':'80'}))
    # extra fields to manage folder state
    #folders = ModelMultipleChoiceField(queryset=Folder.objects.all(), required=False, widget=CheckboxSelectMultiple)

    # override __init__ method to change the querysets for 'parent' and 'peers'
    def __init__(self, *args, **kwargs):

        super(ProjectForm, self ).__init__(*args,**kwargs) # populates the post

        if 'instance' in kwargs:
            instance = kwargs.get('instance')
            current_site = Site.objects.get_current()
            # exclude the project itself, and all its children
            queryset1 =  ~Q(id=instance.id)
            # exclude projects from disabled peer sites
            queryset2 = Q(site__id=current_site.id) | Q(site__peersite__enabled = True)
            # FIXME ? Should children be excluded from list of possible parents ?
            # exclude children from parents
            #for child in instance.children():
            #    parentQueryset = parentQueryset & ~Q(id=child.id)
            # make the ordering case=independent (NOTE: the generated SQL is database-dependent!)
            #self.fields['parents'].queryset =  Project.objects.filter( parentQueryset ).distinct().order_by('short_name')
            self.fields['parents'].queryset =  Project.objects.filter( queryset1 ).filter( queryset2 ).distinct().extra( select={'snl':'lower(short_name)'}, order_by = ['snl'] )
            # peer query-set options: exclude the project itself
            #self.fields['peers'].queryset =  Project.objects.filter( ~Q(id=instance.id) ).distinct().order_by('short_name')
            self.fields['peers'].queryset =  Project.objects.filter( queryset1 ).filter( queryset2 ).distinct().extra( select={'snl':'lower(short_name)'}, order_by = ['snl'] )

            #self.fields['folders'].queryset = Folder.objects.filter(project=instance)
            #self.fields['folders'].queryset = instance.folder_set

    # overridden validation method for project short name
    def clean_short_name(self):
        short_name = self.cleaned_data['short_name']

        # must not start with any of the URL matching patterns
        if short_name in ('admin', 'project', 'news', 'post', 'doc', 'signal'):
            raise forms.ValidationError("Sorry, '%s' is a reserved URL keyword - it cannot be used as project short name" % short_name)

        # only allows letters, numbers, '-' and '_'
        if re.search("[^a-zA-Z0-9_\-]", short_name):
            raise forms.ValidationError("Project short name contains invalid characters")

        # do not allow new projects to have the same short name as existing ones, regardless to case
        if self.instance.id is None: # new projects only
            try:
                p = Project.objects.get(short_name__iexact=short_name)
                raise forms.ValidationError("The new project short name conflicts with an existing project: %s" % p.short_name)
            except Project.DoesNotExist:
                pass

        return short_name


    class Meta:
        model = Project
        # Note: must exclude the many2many field mapped through an intermediary table
        exclude = ('topics','mission','values','vision','history','taskPrioritizationStrategy','requirementsIdentificationProcess','governanceOverview',
                   'developmentOverview',
                   'software_features', 'system_requirements',
                   'getting_started',
                   'projectContacts', 'technicalSupport', 'meetingSupport', 'getInvolved',)


class ContactusForm(ModelForm):

    # overridden validation method for project short name
    def clean_projectContacts(self):
        value = self.cleaned_data['projectContacts']
        if not hasText(value):
            raise forms.ValidationError("Project Contacts cannot be empty")
        return value

    class Meta:
        model = Project
        fields = ('projectContacts', 'technicalSupport', 'meetingSupport', 'getInvolved')
        widgets = { 'projectContacts': Textarea(attrs={'rows':6}),
                    'technicalSupport': Textarea(attrs={'rows':6}),
                    'meetingSupport': Textarea(attrs={'rows':6}),
                    'getInvolved': Textarea(attrs={'rows':6}), }

class DevelopmentOverviewForm(ModelForm):

    class Meta:
        model = Project
        widgets = {'developmentOverview': Textarea(attrs={'rows':6})}
        fields = ('developmentOverview',)

class SoftwareForm(ModelForm):

    class Meta:
        model = Project
        widgets = {'software_features': Textarea(attrs={'rows':6}),
                   'system_requirements': Textarea(attrs={'rows':4}),
                   'license': Textarea(attrs={'rows':4}),
                   'implementationLanguage': Textarea(attrs={'rows':4}),
                   'bindingLanguage': Textarea(attrs={'rows':4}),
                   'supportedPlatforms': Textarea(attrs={'rows':4}),
                   'externalDependencies': Textarea(attrs={'rows':4}),
                   }
        fields = ( 'software_features', 'system_requirements', 'license',
                   'implementationLanguage', 'bindingLanguage','supportedPlatforms', 'externalDependencies')

    def clean(self):
        features = self.cleaned_data.get('software_features')
        if not hasText(features):
            self._errors["software_features"] = self.error_class(["'SoftwareFeatures' must not be empty."])
            print 'error'
        return self.cleaned_data

class UsersForm(ModelForm):

    class Meta:
        model = Project
        widgets = { 'getting_started': Textarea(attrs={'rows':10}), }
        fields = ( 'getting_started', )

class ProjectTagForm(ModelForm):

    # additional field to select existing tags
    tags = ModelMultipleChoiceField(queryset=ProjectTag.objects.all(), required=False)

    def clean(self):
        name = self.cleaned_data['name']

        try:
            tag = ProjectTag.objects.get(name__iexact=name)
            # check tag with same name (independently of case) does not exist already
            if tag is not None and tag.id != self.instance.id: # not this tag
                self._errors["name"] = self.error_class(["Tag with this name already exist: %s" % tag.name])
        except ObjectDoesNotExist :
            # capitalize the tag name
            self.cleaned_data['name'] = self.cleaned_data['name'].capitalize()
            # only allow letters, numbers, '-' and '_'
            if re.search("[^a-zA-Z0-9_\-\s]", name):
                self._errors["name"] = self.error_class(["Tag name contains invalid characters"])
            # impose maximum length
            if len(name)>MAX_PROJECT_TAG_LENGTH:
                self._errors["name"] = self.error_class(["Tag name must contain at most %s characters" % MAX_PROJECT_TAG_LENGTH])

        return self.cleaned_data

    class Meta:
        model = ProjectTag