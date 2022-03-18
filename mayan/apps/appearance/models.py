import bleach

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from mayan.apps.databases.model_mixins import ExtraDataModelMixin
from mayan.apps.events.classes import EventManagerSave
from mayan.apps.events.decorators import method_event

from .events import event_theme_created, event_theme_edited

#import RGBColorFie to create GUI select color
from colorful.fields import RGBColorField

#import os for read files
from os import listdir
from os.path import isfile, join

from django.utils.safestring import mark_safe

class Theme(ExtraDataModelMixin, models.Model):
    label = models.CharField(
        db_index=True, help_text=_('A short text describing the theme.'),
        max_length=128, unique=True, verbose_name=_('Theme')
    )
    #add color code to model

    logoLink = models.CharField(
        db_index=True, help_text=_('Insert Logo with URL link.'),
        max_length=2000, unique=True, verbose_name=_('Logo link')
    )

    fontLink = models.CharField(
        db_index=True, help_text=_('Insert font name from google font.'),
        max_length=2000, unique=True, verbose_name=_('Font name') 
    )

    mmColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Main menu color.'),
        verbose_name=_('Main menu color')
    )

    smmColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Content page color.'),
        verbose_name=_('Content page color')
    )

    hlColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Button Color.'),
        verbose_name=_('Button Color')
    )

    bgColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Backgroud pages color.'),
        verbose_name=_('Backgroud pages color.')
    )

    mtColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Common text color.'),
        verbose_name=_('Common text color.')
    )

    htColor = RGBColorField(
        help_text=_('Select color in panel to change the color of Hint text color.'),
        verbose_name=_('Hint text color.')
    )

    bdtColor = RGBColorField(
        help_text=_('Select color in panel to change the color of title text color.'),
        verbose_name=_('title text color.')
    )

    frameColor = RGBColorField(
        help_text=_('Select color in panel to change the color of frame color.'),
        verbose_name=_('frame color.')
    )

    stylesheet = models.TextField(
        blank=True, help_text=_(
            'The CSS stylesheet to change the appearance of the different'
            'user interface elements.'
        ), verbose_name=_('Stylesheet')
    )

    class Meta:
        ordering = ('label',)
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')

    def __str__(self):
        return force_text(s=self.label)

    def get_absolute_url(self):
        return reverse(
            viewname='appearance:theme_edit', kwargs={
                'theme_id': self.pk
            }
        )

    @method_event(
        event_manager_class=EventManagerSave,
        created={
            'event': event_theme_created,
            'target': 'self',
        },
        edited={
            'event': event_theme_edited,
            'target': 'self',
        }
    )
    def save(self, *args, **kwargs):
        mmColor = self.mmColor
        smmColor = self.smmColor
        hlColor = self.hlColor
        mtColor = self.mtColor
        htColor = self.htColor
        bgColor = self.bgColor
        bdtColor = self.bdtColor
        frameColor = self.frameColor
        fontLink = self.fontLink
        
        css = f"""

        /* change theme */

        .container-fluid {{
            background-color: {mmColor};
        }}
        .btn-block{{
            background-color: {mmColor};
            border: 1px solid {mmColor};            
        }}
        .btn.btn-primary.btn-xs  {{
            background-color: {mmColor};
        }}
        .btn.btn-primary  {{
            background-color: {mmColor};
            border: 1px solid {mmColor};            
        }}
        
        .list-group-item.btn-sm.active {{
            background-color: {mmColor};
        }}
        .list-group-item.btn-sm.active {{
            background-color: {mmColor};
        }}
        #menu-main {{
            background-color: {mmColor};
        }}
        .panel-heading {{
            background-color: {mmColor};
        }} 
        .panel-primary>.panel-heading {{
            background-color: {mmColor};
            border-color: {mmColor};
        }}
        .list-group-item.active {{
            background-color: {mmColor};
        }}
        .nav.navbar-nav.navbar-right li.dropdown.open ul.dropdown-menu a:hover {{
            background: {mmColor};
        }} 
        #accordion-sidebar .panel-heading {{
            background-color: {mmColor};
        }}
        #accordion-sidebar  .panel  div  .panel-body {{
            background-color: {mmColor};
            transition: .1s ease;
        }}
        
        #accordion-sidebar a[aria-expanded="true"] {{
            background-color: {smmColor};
        }}

        .navbar-default .navbar-nav>li>a:hover, .navbar-default .navbar-nav>li>a:focus {{
            color: {smmColor};
            background-color: transparent;
        }}
        #accordion-sidebar > .panel > div > .panel-body > ul > li:hover {{
            background-color: {smmColor};
            transition: .1s ease;
        }}
        .btn-block:hover {{
            background: {smmColor};
        }}
        #accordion-sidebar .panel-heading:hover {{
            background-color: {smmColor};
            transition: .1s ease;
        }}
        .dropdown-menu li a {{
            color: {smmColor};
        }}
        .list-group-item.active:hover {{
            background-color: {smmColor};
        }}
        .text-center.link-text-span.menu-user-name {{
            color: {smmColor};
        }}
        .active.a-main-menu-accordion-link {{
            background-color: {smmColor};
        }}
        #accordion-sidebar > .panel > div > .panel-body > ul > li.active {{
            background: {smmColor};
        }}
        .nav.navbar-nav.navbar-right li.dropdown.open a[aria-expanded="true"] {{
            background: {smmColor};
        }}
        h3#content-title {{
            color: {smmColor};
        }}
        
        div.toast.toast-success {{
            background: {smmColor};
        }}
        .well .panel-primary .panel-heading{{
            background: {smmColor};
        }}
        
        .input-group-btn .btn-default {{
            background-color: {hlColor};
            border: 1px solid {hlColor};
        }}
        .btn.btn-default.btn-outline.btn-xs {{
            background-color: {hlColor};
            border: 1px solid {hlColor};
        }}
        .btn.btn-default.btn-sm {{
            background-color: {hlColor};
            border: 1px solid {hlColor};
        }}
        .well table span a, td a {{
            color: {hlColor};
        }}
        .well table span a, td a:hover {{
            color: {hlColor};
        }}
        .well .panel-heading, .well .svg, .well div > i svg{{
            color: {hlColor};
        }}
        
        body {{
            background-color: {bgColor};
        }}
        
        
        .well div.panel-footer {{
            background: {smmColor}; 
            color: {htColor}; 
        }}
        div.form-group p.help-block {{
            color: {htColor};
        }}

        
        td.last .btn-list a.btn-primary {{
            color: {mtColor};
        }}
        div.form-group {{
            color: {mtColor};
        }}
        
        
        td.last .btn-list a.btn-default {{
            color: {bdtColor};
        }}
        h3#content-title {{
            color: {bdtColor};
        }}
        div.text-center {{
            color: {bdtColor};
        }}

        
        div.well {{
            background: {frameColor};
        }}

        /* change font */

        *{{
            font-family: '{fontLink}', sans-serif !important;
        }}

        """
        self.stylesheet = css
        super().save(*args, **kwargs)


class UserThemeSetting(models.Model):
    user = models.OneToOneField(
        on_delete=models.CASCADE, related_name='theme_settings',
        to=settings.AUTH_USER_MODEL, verbose_name=_('User')
    )
    theme = models.ForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        related_name='user_setting', to=Theme, verbose_name=_('Theme')
    )

    class Meta:
        verbose_name = _('User theme setting')
        verbose_name_plural = _('User theme settings')

    def __str__(self):
        return force_text(s=self.user)

class CurrentTheme(models.Model):
    theme = models.ForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        related_name='CurrentTheme', to=Theme, verbose_name=_('CurrentTheme')
    )

    class Meta:
        verbose_name = _('CurrentTheme')
        verbose_name_plural = _('CurrentTheme')

    def __str__(self): 
        return force_text(s=self.theme)

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)
