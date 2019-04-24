from __future__ import absolute_import, unicode_literals

import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from mayan.apps.permissions.models import Role, StoredPermission

from .managers import AccessControlListManager

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class AccessControlList(models.Model):
    """
    ACL means Access Control List it is a more fine-grained method of
    granting access to objects. In the case of ACLs, they grant access using
    3 elements: actor, permission, object. In this case the actor is the role,
    the permission is the Mayan permission and the object can be anything:
    a document, a folder, an index, etc. This means = "Grant X permissions
    to role Y for object Z". This model holds the permission, object, actor
    relationship for one access control list.
    Fields:
    * Role - Custom role that is being granted a permission. Roles are created
    in the Setup menu.
    """
    content_type = models.ForeignKey(
        on_delete=models.CASCADE, related_name='object_content_type',
        to=ContentType
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(
        ct_field='content_type', fk_field='object_id',
    )
    # TODO: limit choices to the permissions valid for the content_object
    permissions = models.ManyToManyField(
        blank=True, related_name='acls', to=StoredPermission,
        verbose_name=_('Permissions')
    )
    role = models.ForeignKey(
        on_delete=models.CASCADE, related_name='acls', to=Role,
        verbose_name=_('Role')
    )

    objects = AccessControlListManager()

    class Meta:
        ordering = ('pk',)
        unique_together = ('content_type', 'object_id', 'role')
        verbose_name = _('Access entry')
        verbose_name_plural = _('Access entries')

    def __str__(self):
        return _(
            'Role "%(role)s" permission\'s for "%(object)s"'
        ) % {
            'object': self.content_object,
            'role': self.role,
        }

    def get_absolute_url(self):
        return reverse(
            viewname='acls:acl_permissions', kwargs={'pk': self.pk}
        )

    def get_inherited_permissions(self):
        return AccessControlList.objects.get_inherited_permissions(
            role=self.role, obj=self.content_object
        )
