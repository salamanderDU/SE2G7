import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from mayan.apps.acls.models import AccessControlList
from mayan.apps.documents.models import Document

from ..managers import ValidWorkflowInstanceManager
from ..permissions import permission_workflow_transition

from .workflow_models import Workflow
from .workflow_transition_models import (
    WorkflowTransition, WorkflowTransitionField
)

__all__ = ('WorkflowInstance', 'WorkflowInstanceLogEntry')
logger = logging.getLogger(name=__name__)


class WorkflowInstance(models.Model):
    workflow = models.ForeignKey(
        on_delete=models.CASCADE, related_name='instances', to=Workflow,
        verbose_name=_('Workflow')
    )
    document = models.ForeignKey(
        on_delete=models.CASCADE, related_name='workflows', to=Document,
        verbose_name=_('Document')
    )
    context = models.TextField(
        blank=True, verbose_name=_('Context')
    )

    objects = models.Manager()
    valid = ValidWorkflowInstanceManager()

    class Meta:
        ordering = ('workflow',)
        unique_together = ('document', 'workflow')
        verbose_name = _('Workflow instance')
        verbose_name_plural = _('Workflow instances')

    def __str__(self):
        return force_text(s=getattr(self, 'workflow', 'WI'))

    def do_transition(self, transition, comment=None, extra_data=None, user=None):
        with transaction.atomic():
            try:
                if transition in self.get_current_state().origin_transitions.all():
                    if extra_data:
                        context = self.loads()
                        context.update(extra_data)
                        self.dumps(context=context)

                    self.log_entries.create(
                        comment=comment or '',
                        extra_data=json.dumps(obj=extra_data or {}),
                        transition=transition, user=user
                    )
            except AttributeError:
                # No initial state has been set for this workflow
                if settings.DEBUG:
                    raise

    def dumps(self, context):
        """
        Serialize the context data.
        """
        self.context = json.dumps(obj=context)
        self.save()

    def get_absolute_url(self):
        return reverse(
            viewname='document_states:workflow_instance_detail', kwargs={
                'workflow_instance_id': self.pk
            }
        )

    def get_context(self):
        # Keep the document instance in the workflow instance fresh when
        # there are cascade state actions, where a second state action is
        # triggered by the events generated by a first state action.
        self.document.refresh_from_db()
        context = {
            'document': self.document, 'workflow': self.workflow,
            'workflow_instance': self,
        }
        context['workflow_instance_context'] = self.loads()
        return context

    def get_current_state(self):
        """
        Actual State - The current state of the workflow. If there are
        multiple states available, for example: registered, approved,
        archived; this field will tell at the current state where the
        document is right now.
        """
        try:
            return self.get_last_transition().destination_state
        except AttributeError:
            return self.workflow.get_initial_state()

    def get_last_log_entry(self):
        try:
            return self.log_entries.order_by('datetime').last()
        except AttributeError:
            return None

    def get_last_transition(self):
        """
        Last Transition - The last transition used by the last user to put
        the document in the actual state.
        """
        try:
            return self.get_last_log_entry().transition
        except AttributeError:
            return None

    def get_runtime_context(self):
        """
        Alias of self.load() to get just the runtime context of the instance
        for ease of use in the condition template.
        """
        return self.loads()

    def get_transition_choices(self, _user=None):
        current_state = self.get_current_state()

        if current_state:
            queryset = current_state.origin_transitions.all()

            if _user:
                try:
                    """
                    Check for ACL access to the workflow, if true, allow
                    all transition options.
                    """
                    AccessControlList.objects.check_access(
                        obj=self.workflow,
                        permissions=(permission_workflow_transition,),
                        user=_user
                    )
                except PermissionDenied:
                    """
                    If not ACL access to the workflow, filter transition
                    options by each transition ACL access
                    """
                    queryset = AccessControlList.objects.restrict_queryset(
                        permission=permission_workflow_transition,
                        queryset=queryset,
                        user=_user
                    )

            # Remove the transitions with a false return value
            for entry in queryset:
                if not entry.evaluate_condition(workflow_instance=self):
                    queryset = queryset.exclude(id=entry.pk)

            return queryset
        else:
            """
            This happens when a workflow has no initial state and a document
            whose document type has this workflow is created. We return an
            empty transition queryset.
            """
            return WorkflowTransition.objects.none()

    def loads(self):
        """
        Deserialize the context data.
        """
        return json.loads(s=self.context or '{}')


class WorkflowInstanceLogEntry(models.Model):
    """
    Fields:
    * user - The user who last transitioned the document from a state to the
    Actual State.
    * datetime - Date Time - The date and time when the last user transitioned
    the document state to the Actual state.
    """
    workflow_instance = models.ForeignKey(
        on_delete=models.CASCADE, related_name='log_entries',
        to=WorkflowInstance, verbose_name=_('Workflow instance')
    )
    datetime = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_('Datetime')
    )
    transition = models.ForeignKey(
        on_delete=models.CASCADE, to='WorkflowTransition',
        verbose_name=_('Transition')
    )
    user = models.ForeignKey(
        blank=True, null=True, on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL, verbose_name=_('User')
    )
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    extra_data = models.TextField(blank=True, verbose_name=_('Extra data'))

    class Meta:
        ordering = ('datetime',)
        verbose_name = _('Workflow instance log entry')
        verbose_name_plural = _('Workflow instance log entries')

    def __str__(self):
        return force_text(s=self.transition)

    def clean(self):
        if self.transition not in self.workflow_instance.get_transition_choices(_user=self.user):
            raise ValidationError(_('Not a valid transition choice.'))

    def get_extra_data(self):
        result = {}
        for key, value in self.loads().items():
            try:
                field = self.transition.fields.get(name=key)
            except WorkflowTransitionField.DoesNotExist:
                """
                There is a reference for a field that does not exist or
                has been deleted.
                """
            else:
                result[field.label] = value

        return result

    def loads(self):
        """
        Deserialize the context data.
        """
        return json.loads(s=self.extra_data or '{}')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            result = super().save(*args, **kwargs)
            context = self.workflow_instance.get_context()
            context.update(
                {
                    'entry_log': self
                }
            )

            for action in self.transition.origin_state.exit_actions.filter(enabled=True):
                context.update(
                    {
                        'action': action,
                    }
                )
                action.execute(
                    context=context, workflow_instance=self.workflow_instance
                )

            for action in self.transition.destination_state.entry_actions.filter(enabled=True):
                context.update(
                    {
                        'action': action,
                    }
                )
                action.execute(
                    context=context, workflow_instance=self.workflow_instance
                )

            return result
