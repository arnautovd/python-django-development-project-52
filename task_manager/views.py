from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import StatusForm, UserCreateForm, UserLoginForm, UserUpdateForm
from .models import Status

User = get_user_model()


def home(request):
    return render(request, 'tasks/home.html')


class UserListView(ListView):
    model = User
    template_name = 'users.html'
    context_object_name = 'users'
    ordering = ('username',)


class UserCreateView(SuccessMessageMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'user_create.html'
    success_url = reverse_lazy('login')
    success_message = 'Пользователь успешно зарегистрирован'


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'user_update.html'
    success_url = reverse_lazy('users')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.pk != kwargs['pk']:
            messages.error(request, 'У вас нет прав для изменения')
            return HttpResponseRedirect(reverse_lazy('users'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Пользователь успешно изменен')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'user_delete.html'
    success_url = reverse_lazy('users')

    def form_valid(self, form):
        messages.success(self.request, 'Пользователь успешно удален')
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        messages.success(self.request, 'Вы залогинены')
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('home')

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'Вы разлогинены')
        return response


class StatusListView(LoginRequiredMixin, ListView):
    model = Status
    template_name = 'statuses.html'
    context_object_name = 'statuses'


class StatusCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Status
    form_class = StatusForm
    template_name = 'status_create.html'
    success_url = reverse_lazy('statuses')
    success_message = 'Статус успешно создан'


class StatusUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Status
    form_class = StatusForm
    template_name = 'status_update.html'
    success_url = reverse_lazy('statuses')
    success_message = 'Статус успешно изменен'


class StatusDeleteView(LoginRequiredMixin, DeleteView):
    model = Status
    template_name = 'status_delete.html'
    success_url = reverse_lazy('statuses')

    def form_valid(self, form):
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, 'Невозможно удалить статус')
            return redirect('statuses')

        messages.success(self.request, 'Статус успешно удален')
        return redirect(self.get_success_url())
