import django_filters
from django import forms
from django.contrib.auth import get_user_model

from .models import Label, Status, Task

User = get_user_model()


class TaskFilter(django_filters.FilterSet):
    status = django_filters.ModelChoiceFilter(
        queryset=Status.objects.all(),
        label='Статус',
    )
    executor = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        label='Исполнитель',
    )
    label = django_filters.ModelChoiceFilter(
        field_name='labels',
        queryset=Label.objects.all(),
        label='Метка',
    )
    self_tasks = django_filters.BooleanFilter(
        method='filter_self_tasks',
        label='Только свои задачи',
        widget=forms.CheckboxInput,
    )

    class Meta:
        model = Task
        fields = ('status', 'executor', 'label', 'self_tasks')

    def filter_self_tasks(self, queryset, name, value):
        if value and self.request is not None:
            return queryset.filter(author=self.request.user)
        return queryset
